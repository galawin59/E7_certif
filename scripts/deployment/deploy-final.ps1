# DEPLOIEMENT DATA LAKE FICP COMPLET
Import-Module Az.Accounts -Force
Import-Module Az.Resources -Force

Write-Host "DEPLOIEMENT DATA LAKE FICP" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

$resourceGroupName = "rg-datalake-ficp"
$location = "France Central"

# Template ARM simple pour Data Lake
$template = @'
{
    "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
    "contentVersion": "1.0.0.0",
    "parameters": {
        "location": {
            "type": "string",
            "defaultValue": "[resourceGroup().location]"
        }
    },
    "variables": {
        "storageAccountName": "[concat('ficp', uniqueString(resourceGroup().id))]",
        "dataFactoryName": "[concat('df-ficp-', uniqueString(resourceGroup().id))]"
    },
    "resources": [
        {
            "type": "Microsoft.Storage/storageAccounts",
            "apiVersion": "2022-09-01",
            "name": "[variables('storageAccountName')]",
            "location": "[parameters('location')]",
            "sku": {
                "name": "Standard_LRS"
            },
            "kind": "StorageV2",
            "properties": {
                "isHnsEnabled": true,
                "accessTier": "Hot",
                "supportsHttpsTrafficOnly": true
            }
        },
        {
            "type": "Microsoft.DataFactory/factories",
            "apiVersion": "2018-06-01",
            "name": "[variables('dataFactoryName')]",
            "location": "[parameters('location')]",
            "properties": {}
        }
    ],
    "outputs": {
        "storageAccountName": {
            "type": "string",
            "value": "[variables('storageAccountName')]"
        },
        "dataFactoryName": {
            "type": "string",
            "value": "[variables('dataFactoryName')]"
        }
    }
}
'@

# Sauvegarde du template
$templateFile = ".\template.json"
$template | Out-File -FilePath $templateFile -Encoding UTF8

Write-Host "Deploiement en cours..." -ForegroundColor Yellow

try {
    $deployment = New-AzResourceGroupDeployment -ResourceGroupName $resourceGroupName -TemplateFile $templateFile -location $location
    
    Write-Host "SUCCES ! Data Lake deploye :" -ForegroundColor Green
    Write-Host "-> Storage: $($deployment.Outputs.storageAccountName.Value)" -ForegroundColor White
    Write-Host "-> Data Factory: $($deployment.Outputs.dataFactoryName.Value)" -ForegroundColor White
    Write-Host "CERTIFICATION E7 REUSSIE !" -ForegroundColor Green
    
} catch {
    Write-Host "ERREUR: $($_.Exception.Message)" -ForegroundColor Red
}