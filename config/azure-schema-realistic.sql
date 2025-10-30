-- =============================================
-- SCHÉMA AZURE SQL DATABASE - CONSULTATION FICP RÉALISTE
-- Crédit Agricole / LCL / Sofinco
-- =============================================

-- Table des consultations FICP réalistes
CREATE TABLE ConsultationsFICPRealiste (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    DateConsultation DATE NOT NULL,
    CleBDF CHAR(13) NOT NULL,  -- Clé BDF exactement 13 caractères
    ReponseRegistre VARCHAR(20) NOT NULL,  -- INSCRIT ou NON_INSCRIT
    EtablissementDemandeur VARCHAR(100) NOT NULL,
    HeureConsultation TIME,
    DateCreation DATETIME2 DEFAULT GETDATE(),
    
    INDEX IX_ConsultationsFICPRealiste_Date (DateConsultation),
    INDEX IX_ConsultationsFICPRealiste_CleBDF (CleBDF),
    INDEX IX_ConsultationsFICPRealiste_Reponse (ReponseRegistre),
    INDEX IX_ConsultationsFICPRealiste_Etablissement (EtablissementDemandeur)
);

-- Table des inscriptions FICP (vrais incidents)
CREATE TABLE InscriptionsFICP (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    DateInscription DATE NOT NULL,
    CleBDF CHAR(13) NOT NULL,
    TypeIncident VARCHAR(50) NOT NULL,  -- Impayé, Découvert, etc.
    MontantIncident DECIMAL(12,2),
    OrganismeDeclarant VARCHAR(100) NOT NULL,
    StatutInscription VARCHAR(30) DEFAULT 'ACTIVE',  -- ACTIVE, RADIEE
    DateRadiation DATE NULL,
    DateCreation DATETIME2 DEFAULT GETDATE(),
    
    INDEX IX_InscriptionsFICP_Date (DateInscription),
    INDEX IX_InscriptionsFICP_CleBDF (CleBDF),
    INDEX IX_InscriptionsFICP_Statut (StatutInscription)
);

-- Table des radiations FICP réalistes
CREATE TABLE RadiationsFICP (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    DateRadiation DATE NOT NULL,
    CleBDF CHAR(13) NOT NULL,
    TypeRadiation VARCHAR(50) NOT NULL,  -- REGULARISATION_VOLONTAIRE, FIN_DELAI_LEGAL, ERREUR_CONTESTATION
    DateInscriptionOrigine DATE NOT NULL,
    DureeInscriptionJours INT NOT NULL,
    MontantRadie DECIMAL(12,2) DEFAULT 0,
    OrganismeDeclarant VARCHAR(100) NOT NULL,
    MotifDetaille VARCHAR(200),
    StatutRadiation VARCHAR(30) DEFAULT 'VALIDEE',  -- VALIDEE, EN_COURS, REJETEE
    DateCreation DATETIME2 DEFAULT GETDATE(),
    
    INDEX IX_RadiationsFICP_Date (DateRadiation),
    INDEX IX_RadiationsFICP_CleBDF (CleBDF),
    INDEX IX_RadiationsFICP_Type (TypeRadiation),
    INDEX IX_RadiationsFICP_Statut (StatutRadiation)
);

-- Table KPIs Dashboard pour Power BI
CREATE TABLE KPIDashboardFICP (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    DateCalcul DATE NOT NULL,
    
    -- Métriques consultations
    TotalConsultations INT NOT NULL,
    ConsultationsInscrites INT NOT NULL,
    ConsultationsNonInscrites INT NOT NULL,
    TauxInscription DECIMAL(5,2) NOT NULL,
    
    -- Métriques par établissement
    ConsultationsCA INT DEFAULT 0,
    ConsultationsLCL INT DEFAULT 0,
    ConsultationsSofinco INT DEFAULT 0,
    
    -- Métriques temporelles
    ConsultationsMatin INT DEFAULT 0,  -- 8h-12h
    ConsultationsApresMidi INT DEFAULT 0,  -- 12h-18h
    
    DateCreation DATETIME2 DEFAULT GETDATE(),
    
    UNIQUE INDEX UX_KPIDashboardFICP_Date (DateCalcul)
);

-- Vue pour Power BI - Synthèse quotidienne
CREATE VIEW V_SyntheseFICPQuotidienne AS
SELECT 
    DateConsultation,
    EtablissementDemandeur,
    COUNT(*) as NbConsultations,
    SUM(CASE WHEN ReponseRegistre = 'INSCRIT' THEN 1 ELSE 0 END) as NbInscrits,
    SUM(CASE WHEN ReponseRegistre = 'NON_INSCRIT' THEN 1 ELSE 0 END) as NbNonInscrits,
    CAST(
        SUM(CASE WHEN ReponseRegistre = 'INSCRIT' THEN 1.0 ELSE 0 END) * 100.0 / COUNT(*) 
        as DECIMAL(5,2)
    ) as TauxInscription
FROM ConsultationsFICPRealiste
GROUP BY DateConsultation, EtablissementDemandeur;

-- Vue pour Power BI - Évolution mensuelle
CREATE VIEW V_EvolutionFICPMensuelle AS
SELECT 
    YEAR(DateConsultation) as Annee,
    MONTH(DateConsultation) as Mois,
    DATENAME(MONTH, DateConsultation) as NomMois,
    EtablissementDemandeur,
    COUNT(*) as NbConsultations,
    SUM(CASE WHEN ReponseRegistre = 'INSCRIT' THEN 1 ELSE 0 END) as NbInscrits,
    CAST(
        SUM(CASE WHEN ReponseRegistre = 'INSCRIT' THEN 1.0 ELSE 0 END) * 100.0 / COUNT(*) 
        as DECIMAL(5,2)
    ) as TauxInscription
FROM ConsultationsFICPRealiste
GROUP BY YEAR(DateConsultation), MONTH(DateConsultation), 
         DATENAME(MONTH, DateConsultation), EtablissementDemandeur;

-- Procédure stockée pour calcul KPIs automatique
CREATE PROCEDURE sp_CalculerKPIsFICP
    @DateCalcul DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Date par défaut = aujourd'hui
    IF @DateCalcul IS NULL
        SET @DateCalcul = CAST(GETDATE() AS DATE);
    
    -- Supprimer les KPIs existants pour cette date
    DELETE FROM KPIDashboardFICP WHERE DateCalcul = @DateCalcul;
    
    -- Calculer et insérer les nouveaux KPIs
    INSERT INTO KPIDashboardFICP (
        DateCalcul, TotalConsultations, ConsultationsInscrites, 
        ConsultationsNonInscrites, TauxInscription,
        ConsultationsCA, ConsultationsLCL, ConsultationsSofinco,
        ConsultationsMatin, ConsultationsApresMidi
    )
    SELECT 
        @DateCalcul as DateCalcul,
        COUNT(*) as TotalConsultations,
        SUM(CASE WHEN ReponseRegistre = 'INSCRIT' THEN 1 ELSE 0 END) as ConsultationsInscrites,
        SUM(CASE WHEN ReponseRegistre = 'NON_INSCRIT' THEN 1 ELSE 0 END) as ConsultationsNonInscrites,
        CAST(
            SUM(CASE WHEN ReponseRegistre = 'INSCRIT' THEN 1.0 ELSE 0 END) * 100.0 / COUNT(*) 
            as DECIMAL(5,2)
        ) as TauxInscription,
        
        -- Par établissement
        SUM(CASE WHEN EtablissementDemandeur LIKE '%Crédit Agricole%' THEN 1 ELSE 0 END) as ConsultationsCA,
        SUM(CASE WHEN EtablissementDemandeur = 'LCL' THEN 1 ELSE 0 END) as ConsultationsLCL,
        SUM(CASE WHEN EtablissementDemandeur LIKE '%Sofinco%' THEN 1 ELSE 0 END) as ConsultationsSofinco,
        
        -- Par période
        SUM(CASE WHEN CAST(HeureConsultation as TIME) BETWEEN '08:00' AND '12:00' THEN 1 ELSE 0 END) as ConsultationsMatin,
        SUM(CASE WHEN CAST(HeureConsultation as TIME) BETWEEN '12:01' AND '18:00' THEN 1 ELSE 0 END) as ConsultationsApresMidi
        
    FROM ConsultationsFICPRealiste
    WHERE DateConsultation = @DateCalcul;
    
    SELECT 'KPIs calculés pour le ' + CAST(@DateCalcul as VARCHAR(10)) as Resultat;
END;

-- Données d'exemple pour tests
INSERT INTO InscriptionsFICP (DateInscription, CleBDF, TypeIncident, MontantIncident, OrganismeDeclarant)
VALUES 
    ('2025-01-15', 'CLIENTTEST001', 'Impayé crédit', 15000.00, 'Crédit Agricole'),
    ('2025-02-20', 'CLIENTTEST002', 'Découvert persistant', 2500.00, 'LCL'),
    ('2025-03-10', 'CLIENTTEST003', 'Défaillance prêt', 45000.00, 'Sofinco');

PRINT 'Schéma FICP réaliste créé avec succès';
PRINT 'Tables : ConsultationsFICPRealiste, InscriptionsFICP, KPIDashboardFICP';
PRINT 'Vues : V_SyntheseFICPQuotidienne, V_EvolutionFICPMensuelle';
PRINT 'Procédure : sp_CalculerKPIsFICP';