
-- Creation des tables Azure SQL Database
USE [db-ficp-datawarehouse];

-- 1. Table ConsultationsFICP
IF OBJECT_ID('ConsultationsFICP', 'U') IS NOT NULL DROP TABLE ConsultationsFICP;
CREATE TABLE ConsultationsFICP (
    ID BIGINT IDENTITY(1,1) PRIMARY KEY,
    DateConsultation DATE NOT NULL,
    NumeroSIREN NVARCHAR(20) NOT NULL,
    NomEntreprise NVARCHAR(255) NOT NULL,
    MontantDemande DECIMAL(15,2) NOT NULL,
    TypeCredit NVARCHAR(50) NOT NULL,
    StatutDemande NVARCHAR(20) NOT NULL,
    ScoreRisque INT,
    RegionEntreprise NVARCHAR(50),
    SecteurActivite NVARCHAR(100),
    CreatedAt DATETIME2 DEFAULT GETDATE()
);

-- 2. Table InscriptionsFICP
IF OBJECT_ID('InscriptionsFICP', 'U') IS NOT NULL DROP TABLE InscriptionsFICP;
CREATE TABLE InscriptionsFICP (
    ID BIGINT IDENTITY(1,1) PRIMARY KEY,
    DateInscription DATE NOT NULL,
    NumeroSIREN NVARCHAR(20) NOT NULL,
    NomEntreprise NVARCHAR(255) NOT NULL,
    MontantIncident DECIMAL(15,2) NOT NULL,
    TypeIncident NVARCHAR(50) NOT NULL,
    StatutInscription NVARCHAR(20) NOT NULL,
    DureeInscription INT,
    OrganismeDeclarant NVARCHAR(100),
    RegionEntreprise NVARCHAR(50),
    SecteurActivite NVARCHAR(100),
    CreatedAt DATETIME2 DEFAULT GETDATE()
);

-- 3. Table RadiationsFICP
IF OBJECT_ID('RadiationsFICP', 'U') IS NOT NULL DROP TABLE RadiationsFICP;
CREATE TABLE RadiationsFICP (
    ID BIGINT IDENTITY(1,1) PRIMARY KEY,
    DateRadiation DATE NOT NULL,
    NumeroSIREN NVARCHAR(20) NOT NULL,
    NomEntreprise NVARCHAR(255) NOT NULL,
    MontantRembourse DECIMAL(15,2),
    TypeRadiation NVARCHAR(50) NOT NULL,
    StatutRadiation NVARCHAR(20) NOT NULL,
    DureeIncident INT,
    OrganismeValidation NVARCHAR(100),
    RegionEntreprise NVARCHAR(50),
    SecteurActivite NVARCHAR(100),
    CreatedAt DATETIME2 DEFAULT GETDATE()
);

-- 4. Table KPI Dashboard
IF OBJECT_ID('KPIDashboardFICP', 'U') IS NOT NULL DROP TABLE KPIDashboardFICP;
CREATE TABLE KPIDashboardFICP (
    ID BIGINT IDENTITY(1,1) PRIMARY KEY,
    DateCalcul DATE NOT NULL,
    TotalConsultations INT NOT NULL DEFAULT 0,
    MontantTotalDemandes DECIMAL(18,2) NOT NULL DEFAULT 0,
    TauxAcceptation DECIMAL(5,2),
    TotalInscriptions INT NOT NULL DEFAULT 0,
    TotalRadiations INT NOT NULL DEFAULT 0,
    NombreEntreprisesUniques INT,
    CreatedAt DATETIME2 DEFAULT GETDATE()
);

-- Index pour performances
CREATE INDEX IX_Consultations_Date ON ConsultationsFICP(DateConsultation);
CREATE INDEX IX_Consultations_SIREN ON ConsultationsFICP(NumeroSIREN);
CREATE INDEX IX_Inscriptions_Date ON InscriptionsFICP(DateInscription);
CREATE INDEX IX_Radiations_Date ON RadiationsFICP(DateRadiation);

PRINT '✅ SCHEMA AZURE SQL CREE AVEC SUCCES !';
PRINT '📊 4 tables relationnelles pretes';
PRINT '⚡ Index de performance configures';
    