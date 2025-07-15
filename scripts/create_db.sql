-- Script pour créer la base de données PostgreSQL

-- Créer la base de données
CREATE DATABASE gd_ia_comptable;

-- Créer un utilisateur dédié (optionnel)
-- CREATE USER gd_user WITH ENCRYPTED PASSWORD 'password';
-- GRANT ALL PRIVILEGES ON DATABASE gd_ia_comptable TO gd_user;

-- Se connecter à la base
\c gd_ia_comptable;

-- Activer les extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Pour la recherche textuelle