Use PlateformeFormation;
CREATE TABLE Apprenants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nom VARCHAR(100),
    Prenom VARCHAR(100),
    AdresseEmail VARCHAR(150) UNIQUE,
    MotDePasse VARCHAR(255),
    Phone VARCHAR(20),
    Ville VARCHAR(100),
    TypeDeFormation VARCHAR(100),
    CodeCoupon VARCHAR(50),
    DateDebutFormation DATE,
    DateFinFormation DATE,
    Centre VARCHAR(100),
    NiveauDeConnaissance VARCHAR(100)
);

CREATE TABLE ResponsablePedagogique (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nom VARCHAR(100),
    Prenom VARCHAR(100),
    AdresseEmail VARCHAR(150) UNIQUE,
    MotDePasse VARCHAR(255),
    Phone VARCHAR(20),
    Ville VARCHAR(100),
    CodeCoupon VARCHAR(50),
    Centre VARCHAR(100)
);

CREATE TABLE Responsable_de_centre_de_coding (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nom VARCHAR(100),
    Prenom VARCHAR(100),
    AdresseEmail VARCHAR(150) UNIQUE,
    MotDePasse VARCHAR(255),
    Phone VARCHAR(20),
    Ville VARCHAR(100),
    CodeCoupon VARCHAR(50),
    Centre VARCHAR(100)
);

CREATE TABLE Administrateur (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Nom VARCHAR(100),
    Prenom VARCHAR(100),
    AdresseEmail VARCHAR(150) UNIQUE,
    MotDePasse VARCHAR(255)
);

CREATE TABLE Presence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    apprenant_id INT,
    Nom VARCHAR(100),
    Prenom VARCHAR(100),
    AdresseEmail VARCHAR(150),
    Centre VARCHAR(100),
    date_connexion DATE,
    heure_connexion DATETIME,
    heure_deconnexion DATETIME
);

CREATE TABLE PresenceCentre (
    id INT AUTO_INCREMENT PRIMARY KEY,
    apprenant_id INT,
    Nom VARCHAR(100),
    Prenom VARCHAR(100),
    AdresseEmail VARCHAR(150),
    Centre VARCHAR(100),
    date_connexion DATE,
    heure_connexion DATETIME,
    heure_deconnexion DATETIME
);

CREATE TABLE Messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    expediteur_email VARCHAR(150),
    expediteur_role VARCHAR(50),
    destinataire_email VARCHAR(150),
    destinataire_role VARCHAR(50),
    sujet TEXT,
    contenu TEXT,
    lu BOOLEAN DEFAULT FALSE,
    date_envoi DATETIME DEFAULT CURRENT_TIMESTAMP,
    expediteur_supprime BOOLEAN DEFAULT FALSE,
    destinataire_supprime BOOLEAN DEFAULT FALSE
);

--: Insert test users

-- Test Apprenant
INSERT INTO Apprenants (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, TypeDeFormation, CodeCoupon, DateDebutFormation, DateFinFormation, Centre, NiveauDeConnaissance)
VALUES ('Doe', 'John', 'john.apprenant@example.com', 'pass123', '0600000001', 'Rabat', 'IA', 'CODE123', '2025-07-01', '2025-12-31', 'Centre A', 'Débutant');

-- Test Responsable Pédagogique
INSERT INTO ResponsablePedagogique (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, CodeCoupon, Centre)
VALUES ('Smith', 'Anna', 'anna.pedago@example.com', 'pass456', '0600000002', 'Casablanca', 'PEDA456', 'Centre A');

-- Test Responsable de Centre
INSERT INTO Responsable_de_centre_de_coding (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, CodeCoupon, Centre)
VALUES ('Ben', 'Ali', 'ali.coding@example.com', 'pass789', '0600000003', 'Fès', 'CODE789', 'Centre A');

-- Test Administrateur
INSERT INTO Administrateur (Nom, Prenom, AdresseEmail, MotDePasse)
VALUES ('Karim', 'Admin', 'admin@example.com', 'adminpass');

