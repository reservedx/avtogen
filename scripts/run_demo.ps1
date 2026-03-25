$base = "http://127.0.0.1:8000/api/v1"

$payload = @{
  topic_query = "frequent urination with cystitis"
  audience = "general audience"
  cluster_name = "Local Demo Cluster"
} | ConvertTo-Json

$response = Invoke-RestMethod -Method Post -Uri "$base/demo/bootstrap" -ContentType "application/json" -Body $payload

Write-Host ""
Write-Host "Demo bootstrap completed"
Write-Host "Cluster:  $($response.cluster_id)"
Write-Host "Topic:    $($response.topic_id)"
Write-Host "Brief:    $($response.brief_id)"
Write-Host "Article:  $($response.article_id)"
Write-Host "Sources:  $($response.sources_collected)"
Write-Host "Notes:    $($response.research_notes_extracted)"
Write-Host "Images:   $($response.images_generated)"
Write-Host "Quality:  $($response.quality_status) / $($response.quality_score)"
Write-Host "Risk:     $($response.risk_score)"
Write-Host ""
Write-Host "Open admin UI: http://127.0.0.1:3000"
Write-Host "Open article:  http://127.0.0.1:3000/articles/$($response.article_id)"
Write-Host "Open topic:    http://127.0.0.1:3000/topics/$($response.topic_id)"
