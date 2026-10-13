import pathlib

FILES = {
      "backend/LlmPulse.Api/LlmPulse.Api.csproj": """<Project Sdk="Microsoft.NET.Sdk.Web">
        <PropertyGroup>
            <TargetFramework>net8.0</TargetFramework>
                <Nullable>enable</Nullable>
                    <ImplicitUsings>enable</ImplicitUsings>
                      </PropertyGroup>
                        <ItemGroup>
                            <PackageReference Include="MediatR" Version="12.4.1" />
                                <PackageReference Include="FluentValidation.DependencyInjectionExtensions" Version="11.10.0" />
                                    <PackageReference Include="Microsoft.EntityFrameworkCore.Sqlite" Version="8.0.10" />
                                        <PackageReference Include="Swashbuckle.AspNetCore" Version="6.8.1" />
                                          </ItemGroup>
                                          </Project>""",
      "backend/LlmPulse.Api/Domain/LlmModelEvaluation.cs": """namespace LlmPulse.Api.Domain;

      public sealed class LlmModelEvaluation
      {
          public Guid Id { get; set; } = Guid.NewGuid();
              public string Name { get; set; } = string.Empty;
                  public string Provider { get; set; } = string.Empty;
                      public string ParameterSize { get; set; } = string.Empty;
                          public int ContextWindow { get; set; } = 128000;
                              public double MmluScore { get; set; }
                                  public double HumanEvalScore { get; set; }
                                      public double Gsm8kScore { get; set; }
                                          public double IfEvalScore { get; set; }
                                              public double TruthfulQaScore { get; set; }
                                                  public double SafetyScore { get; set; }
                                                      public int TtftMs { get; set; }
                                                          public double TokensPerSecond { get; set; }
                                                              public decimal InputCostPerMillion { get; set; }
                                                                  public decimal OutputCostPerMillion { get; set; }
                                                                      public double OverallScore { get; set; }
                                                                          public string Tier { get; set; } = "C";
                                                                              public string Verdict { get; set; } = "Weak";
                                                                                  public string PrimaryBadge { get; set; } = "General Purpose";
                                                                                      public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;
                                                                                      }""",
      "backend/LlmPulse.Api/Features/Models/Shared/LlmClassificationEngine.cs": """using LlmPulse.Api.Domain;

      namespace LlmPulse.Api.Features.Models.Shared;

      public sealed record CriteriaWeights(double Reasoning = 0.30, double Coding = 0.25, double Safety = 0.15, double Speed = 0.15, double Cost = 0.15)
      {
          public static readonly CriteriaWeights Default = new();
          }

          public sealed record ClassificationResult(double OverallScore, string Tier, string Verdict, string PrimaryBadge, double BlendedCostPerMillion);

          public static class LlmClassificationEngine
          {
              public static ClassificationResult Classify(LlmModelEvaluation m, CriteriaWeights w)
                  {
                          double total = w.Reasoning + w.Coding + w.Safety + w.Speed + w.Cost;
                                  if (total <= 0) total = 1.0;
                                          double reasoningSub = (m.MmluScore * 0.55) + (m.Gsm8kScore * 0.45);
                                                  double codingSub = (m.HumanEvalScore * 0.60) + (m.IfEvalScore * 0.40);
                                                          double safetySub = (m.TruthfulQaScore * 0.60) + (m.SafetyScore * 0.40);
                                                                  double ttftScore = Math.Clamp(100.0 - ((m.TtftMs - 120.0) / 12.0), 0.0, 100.0);
                                                                          double tpsScore = Math.Clamp((m.TokensPerSecond / 150.0) * 100.0, 0.0, 100.0);
                                                                                  double speedSub = (ttftScore * 0.45) + (tpsScore * 0.55);
                                                                                          double blendedCost = (double)((m.InputCostPerMillion * 3m + m.OutputCostPerMillion) / 4m);
                                                                                                  double costSub = Math.Clamp(100.0 - (Math.Log10(blendedCost + 1.0) * 62.0), 5.0, 100.0);
                                                                                                          double overall = ((reasoningSub * w.Reasoning) + (codingSub * w.Coding) + (safetySub * w.Safety) + (speedSub * w.Speed) + (costSub * w.Cost)) / total;
                                                                                                                  var (tier, verdict) = overall switch { >= 82.0 => ("S", "Elite"), >= 72.0 => ("A", "Good"), >= 60.0 => ("B", "Average"), _ => ("C", "Weak") };
                                                                                                                          string badge = (m.HumanEvalScore >= 88 && m.MmluScore >= 86) ? "Frontier Coding & Reasoning" : (blendedCost <= 0.45 && reasoningSub >= 82) ? "Best Value Champion" : "Balanced Generalist";
                                                                                                                                  return new ClassificationResult(Math.Round(overall, 1), tier, verdict, badge, Math.Round(blendedCost, 2));
                                                                                                                                      }
                                                                                                                                      }""",
      "backend/LlmPulse.Api/Program.cs": """using MediatR;
      using LlmPulse.Api.Domain;
      using LlmPulse.Api.Features.Models.Shared;

      var builder = WebApplication.CreateBuilder(args);
      builder.Services.AddEndpointsApiExplorer();
      builder.Services.AddSwaggerGen();
      builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<Program>());
      builder.Services.AddCors(o => o.AddDefaultPolicy(p => p.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod()));

      var app = builder.Build();
      app.UseCors();
      app.UseSwagger();
      app.UseSwaggerUI();

      var store = new List<LlmModelEvaluation>
      {
          new() { Name = "Claude 3.5 Sonnet", Provider = "Anthropic", ParameterSize = "Frontier Dense", MmluScore = 88.7, HumanEvalScore = 92.0, Gsm8kScore = 96.4, IfEvalScore = 90.2, TruthfulQaScore = 86.5, SafetyScore = 96.0, TtftMs = 410, TokensPerSecond = 78, InputCostPerMillion = 3.0m, OutputCostPerMillion = 15.0m },
              new() { Name = "GPT-4o", Provider = "OpenAI", ParameterSize = "Omni MoE", MmluScore = 88.7, HumanEvalScore = 90.2, Gsm8kScore = 95.8, IfEvalScore = 89.5, TruthfulQaScore = 85.0, SafetyScore = 95.0, TtftMs = 320, TokensPerSecond = 98, InputCostPerMillion = 2.5m, OutputCostPerMillion = 10.0m },
                  new() { Name = "DeepSeek-V2.5", Provider = "DeepSeek", ParameterSize = "236B MoE", MmluScore = 85.0, HumanEvalScore = 89.0, Gsm8kScore = 92.5, IfEvalScore = 84.0, TruthfulQaScore = 79.0, SafetyScore = 88.0, TtftMs = 390, TokensPerSecond = 85, InputCostPerMillion = 0.14m, OutputCostPerMillion = 0.28m }
                  };

                  app.MapGet("/api/models", () => Results.Ok(store.Select(m => new { Model = m, Classification = LlmClassificationEngine.Classify(m, CriteriaWeights.Default) })));
                  app.MapPost("/api/models", (LlmModelEvaluation m) => {
                      m.Id = Guid.NewGuid();
                          var c = LlmClassificationEngine.Classify(m, CriteriaWeights.Default);
                              m.OverallScore = c.OverallScore; m.Tier = c.Tier; m.Verdict = c.Verdict; m.PrimaryBadge = c.PrimaryBadge;
                                  store.Add(m);
                                      return Results.Created($"/api/models/{m.Id}", new { Model = m, Classification = c });
                                      });
                                      app.MapDelete("/api/models/{id:guid}", (Guid id) => { store.RemoveAll(x => x.Id == id); return Results.NoContent(); });

                                      app.Run();""",
      "frontend/package.json": """{
        "name": "llmpulse-frontend",
          "private": true,
            "version": "1.0.0",
              "type": "module",
                "scripts": {
                    "dev": "vite",
                        "build": "vite build"
    },
      "dependencies": {
          "@reduxjs/toolkit": "^2.2.7",
              "react": "^18.3.1",
                  "react-dom": "^18.3.1",
                      "react-redux": "^9.1.2"
    },
      "devDependencies": {
          "@types/react": "^18.3.3",
              "@types/react-dom": "^18.3.0",
                  "@vitejs/plugin-react": "^4.3.1",
                      "typescript": "^5.5.3",
                          "vite": "^5.4.1"
    }
    }"""
}

for rel, content in FILES.items():
      p = pathlib.Path(rel)
      p.parent.mkdir(parents=True, exist_ok=True)
      p.write_text(content, encoding="utf-8")
      print(f"Created {rel}")
