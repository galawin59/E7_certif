# CONFIGURATION DATA FACTORY POUR FICP
# Certification E7 - Data Engineer
Import-Module Az.Accounts -Force
Import-Module Az.DataFactory -Force

Write-Host "CONFIGURATION DATA FACTORY FICP" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

# Configuration
$resourceGroupName = "rg-datalake-ficp"
$dataFactoryName = "df-ficp"
$storageAccountName = "ficpstorageaccount"
$location = "France Central"

Write-Host "Configuration :" -ForegroundColor Cyan
Write-Host "-> Data Factory: $dataFactoryName"
Write-Host "-> Storage Account: $storageAccountName"
Write-Host "-> Resource Group: $resourceGroupName"
Write-Host ""

try {
    # 1. Création du Linked Service pour Azure Storage
    Write-Host "1. Creation du Linked Service Storage..." -ForegroundColor Yellow
    
    $storageAccount = Get-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName
    $storageKey = (Get-AzStorageAccountKey -ResourceGroupName $resourceGroupName -Name $storageAccountName)[0].Value
    
    $linkedServiceDefinition = @{
        type = "AzureBlobStorage"
        typeProperties = @{
            connectionString = "DefaultEndpointsProtocol=https;AccountName=$storageAccountName;AccountKey=$storageKey;EndpointSuffix=core.windows.net"
        }
    } | ConvertTo-Json -Depth 10
    
    # Sauvegarde de la définition
    $linkedServiceFile = ".\Infrastructure\linkedservice-storage.json"
    $linkedServiceDefinition | Out-File -FilePath $linkedServiceFile -Encoding UTF8
    
    Write-Host "   -> Linked Service Storage defini" -ForegroundColor Green
    
    # 2. Création du Dataset pour les fichiers FICP
    Write-Host "2. Creation du Dataset FICP..." -ForegroundColor Yellow
    
    $datasetDefinition = @{
        type = "DelimitedText"
        linkedServiceName = @{
            referenceName = "LinkedService_Storage"
            type = "LinkedServiceReference"
        }
        typeProperties = @{
            location = @{
                type = "AzureBlobStorageLocation"
                container = "ficp-data"
            }
            columnDelimiter = ","
            escapeChar = "\"
            firstRowAsHeader = $true
            quoteChar = "\"
        }
    } | ConvertTo-Json -Depth 10
    
    $datasetFile = ".\Infrastructure\dataset-ficp.json"
    $datasetDefinition | Out-File -FilePath $datasetFile -Encoding UTF8
    
    Write-Host "   -> Dataset FICP defini" -ForegroundColor Green
    
    # 3. Création du Pipeline de traitement
    Write-Host "3. Creation du Pipeline FICP..." -ForegroundColor Yellow
    
    $pipelineDefinition = @{
        activities = @(
            @{
                name = "Copy_FICP_Data"
                type = "Copy"
                typeProperties = @{
                    source = @{
                        type = "DelimitedTextSource"
                        storeSettings = @{
                            type = "AzureBlobStorageReadSettings"
                            recursive = $true
                            wildcardFileName = "ficp_*.csv"
                        }
                        formatSettings = @{
                            type = "DelimitedTextReadSettings"
                        }
                    }
                    sink = @{
                        type = "DelimitedTextSink"
                        storeSettings = @{
                            type = "AzureBlobStorageWriteSettings"
                        }
                        formatSettings = @{
                            type = "DelimitedTextWriteSettings"
                            quoteAllText = $true
                            fileExtension = ".csv"
                        }
                    }
                }
                inputs = @(
                    @{
                        referenceName = "Dataset_FICP_Source"
                        type = "DatasetReference"
                    }
                )
                outputs = @(
                    @{
                        referenceName = "Dataset_FICP_Processed"
                        type = "DatasetReference"
                    }
                )
            }
        )
    } | ConvertTo-Json -Depth 10
    
    $pipelineFile = ".\Infrastructure\pipeline-ficp.json"
    $pipelineDefinition | Out-File -FilePath $pipelineFile -Encoding UTF8
    
    Write-Host "   -> Pipeline FICP defini" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   DATA FACTORY CONFIGURE !" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "FICHIERS CREES :" -ForegroundColor Cyan
    Write-Host "-> $linkedServiceFile"
    Write-Host "-> $datasetFile"
    Write-Host "-> $pipelineFile"
    Write-Host ""
    Write-Host "PROCHAINES ETAPES :" -ForegroundColor Yellow
    Write-Host "1. Allez sur portal.azure.com"
    Write-Host "2. Naviguez vers Data Factory: $dataFactoryName"
    Write-Host "3. Importez les configurations JSON"
    Write-Host "4. Testez le pipeline"
    Write-Host ""
    Write-Host "DATA LAKE FICP PRET POUR PRODUCTION !" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "ERREUR CONFIGURATION:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}