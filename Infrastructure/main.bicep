// ===============================
// DATALAKE FICP - INFRASTRUCTURE BICEP
// Certification Data Engineer C19
// ===============================

@description('Environnement de déploiement')
@allowed(['test', 'prod'])
param environment string = 'test'

@description('Région de déploiement')
param location string = 'francecentral'

@description('Préfixe pour les noms de ressources')
param resourcePrefix string = 'dl-ficp'

@description('Tags communs pour toutes les ressources')
param commonTags object = {
  Environment: environment
  Project: 'DataLake-FICP'
  Owner: 'DataEngineer'
  Purpose: 'Certification'
  CostCenter: 'Training'
}

// ===============================
// VARIABLES
// ===============================
var resourceGroupName = 'rg-${resourcePrefix}-${environment}'
var storageAccountName = '${replace(resourcePrefix, '-', '')}${environment}dl'
var dataFactoryName = 'adf-${resourcePrefix}-${environment}'
var synapseWorkspaceName = 'synapse-${resourcePrefix}-${environment}'
var purviewAccountName = 'purview-${resourcePrefix}-${environment}'
var keyVaultName = 'kv-${resourcePrefix}-${environment}'
var logAnalyticsName = 'log-${resourcePrefix}-${environment}'
var appInsightsName = 'ai-${resourcePrefix}-${environment}'

// ===============================
// DATA LAKE STORAGE GEN2
// ===============================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: commonTags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS' // Optimisation coûts
  }
  properties: {
    isHnsEnabled: true // Data Lake Gen2
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
    networkAcls: {
      defaultAction: 'Allow' // Simplification pour test
      bypass: 'AzureServices'
    }
  }
}

// Conteneurs Data Lake (Bronze/Silver/Gold)
resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 30
    }
  }
}

resource bronzeContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'bronze'
  properties: {
    publicAccess: 'None'
  }
}

resource silverContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'silver'
  properties: {
    publicAccess: 'None'
  }
}

resource goldContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'gold'
  properties: {
    publicAccess: 'None'
  }
}

// ===============================
// KEY VAULT (Secrets)
// ===============================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: commonTags
  properties: {
    tenantId: tenant().tenantId
    sku: {
      family: 'A'
      name: 'standard' // Coût optimisé
    }
    accessPolicies: []
    enableSoftDelete: true
    softDeleteRetentionInDays: 7 // Minimum pour test
    enableRbacAuthorization: true
  }
}

// ===============================
// LOG ANALYTICS & MONITORING
// ===============================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: commonTags
  properties: {
    sku: {
      name: 'PerGB2018' // Pay-as-you-go
    }
    retentionInDays: 30 // Minimum pour coûts
    workspaceCapping: {
      dailyQuotaGb: 1 // Limite pour éviter surcoûts
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: commonTags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// ===============================
// DATA FACTORY
// ===============================
resource dataFactory 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: dataFactoryName
  location: location
  tags: commonTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publicNetworkAccess: 'Enabled' // Simplification pour test
  }
}

// Linked Service vers Storage Account
resource storageLinkedService 'Microsoft.DataFactory/factories/linkedservices@2018-06-01' = {
  parent: dataFactory
  name: 'AzureDataLakeStorage'
  properties: {
    type: 'AzureBlobFS'
    typeProperties: {
      url: storageAccount.properties.primaryEndpoints.dfs
    }
  }
}

// ===============================
// SYNAPSE ANALYTICS WORKSPACE
// ===============================
resource synapseWorkspace 'Microsoft.Synapse/workspaces@2021-06-01' = {
  name: synapseWorkspaceName
  location: location
  tags: commonTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    defaultDataLakeStorage: {
      accountUrl: storageAccount.properties.primaryEndpoints.dfs
      filesystem: silverContainer.name
    }
    sqlAdministratorLogin: 'sqladmin'
    sqlAdministratorLoginPassword: 'P@ssw0rd123!' // À changer via Key Vault
    publicNetworkAccess: 'Enabled'
  }
}

// Pare-feu Synapse (accès depuis Azure)
resource synapseFirewall 'Microsoft.Synapse/workspaces/firewallRules@2021-06-01' = {
  parent: synapseWorkspace
  name: 'AllowAllWindowsAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ===============================
// AZURE PURVIEW
// ===============================
resource purviewAccount 'Microsoft.Purview/accounts@2021-12-01' = {
  name: purviewAccountName
  location: location
  tags: commonTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    managedResourceGroupName: '${resourceGroupName}-purview-managed'
  }
}

// ===============================
// RBAC ASSIGNMENTS
// ===============================

// Data Factory -> Storage Blob Data Contributor
resource adfStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, dataFactory.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: dataFactory.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Synapse -> Storage Blob Data Contributor  
resource synapseStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, synapseWorkspace.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: synapseWorkspace.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Purview -> Storage Blob Data Reader
resource purviewStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, purviewAccount.id, '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1') // Storage Blob Data Reader
    principalId: purviewAccount.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ===============================
// OUTPUTS
// ===============================
output storageAccountName string = storageAccount.name
output storageAccountUrl string = storageAccount.properties.primaryEndpoints.dfs
output dataFactoryName string = dataFactory.name
output synapseWorkspaceName string = synapseWorkspace.name
output purviewAccountName string = purviewAccount.name
output keyVaultName string = keyVault.name
output resourceGroupName string = resourceGroupName

// URLs d'accès
output synapseStudioUrl string = 'https://${synapseWorkspace.name}.dev.azuresynapse.net'
output purviewStudioUrl string = 'https://web.purview.azure.com/resource/${purviewAccount.name}'
output dataFactoryUrl string = 'https://adf.azure.com/en/home?factory=${dataFactory.name}'

// Estimation coûts
output estimatedMonthlyCost string = 'Storage: ~1€ | Data Factory: ~2€ | Synapse: ~1€ | Purview: ~3€ | Total: ~7€'