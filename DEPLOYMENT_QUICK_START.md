# Guide Rapide de Déploiement OVH

## 🚀 Déploiement en 5 étapes

### 1️⃣ Préparer le serveur OVH
```bash
# Sur votre serveur OVH
wget https://raw.githubusercontent.com/votre-repo/gd-ia-comptable/main/scripts/setup-ovh-server.sh
chmod +x setup-ovh-server.sh
./setup-ovh-server.sh
```

### 2️⃣ Déployer l'application
```bash
# Depuis votre machine locale
./scripts/deploy-to-ovh.sh -h VOTRE_IP_OVH
```

### 3️⃣ Configurer les variables d'environnement
```bash
# Sur le serveur OVH
cd /opt/gd-ia-comptable
cp .env.production.example .env.production
nano .env.production  # Modifier les valeurs
```

### 4️⃣ Configurer le domaine et SSL
```bash
# Modifier la configuration Nginx
nano /etc/nginx/sites-available/normx-docs
# Remplacer 'votre-domaine.com' par votre domaine

# Activer SSL
certbot --nginx -d votre-domaine.com
```

### 5️⃣ Démarrer l'application
```bash
cd /opt/gd-ia-comptable
docker-compose -f docker-compose.production.yml up -d
```

## ✅ Vérification

1. **Vérifier les services**
   ```bash
   docker-compose -f docker-compose.production.yml ps
   ```

2. **Accéder à l'application**
   - Frontend: https://votre-domaine.com
   - API Docs: https://votre-domaine.com/docs

3. **Voir les logs**
   ```bash
   docker-compose -f docker-compose.production.yml logs -f
   ```

## 🔧 Commandes Utiles

### Mise à jour
```bash
./scripts/deploy-to-ovh.sh -h VOTRE_IP_OVH
```

### Sauvegarde manuelle
```bash
/opt/backup-normx.sh
```

### Redémarrer les services
```bash
docker-compose -f docker-compose.production.yml restart
```

### Nettoyer les ressources Docker
```bash
docker system prune -a
```

## ⚠️ Points d'Attention

1. **Sécurité**
   - Changez TOUS les mots de passe par défaut
   - Configurez le firewall (ufw)
   - Désactivez l'accès root SSH après configuration

2. **Performance**
   - Ajustez les workers selon vos besoins
   - Configurez les limites de ressources Docker
   - Surveillez l'utilisation CPU/RAM

3. **Sauvegardes**
   - Vérifiez que les sauvegardes automatiques fonctionnent
   - Testez la restauration régulièrement
   - Considérez une réplication hors-site

## 📞 Support

En cas de problème :
1. Consultez les logs : `docker-compose logs`
2. Vérifiez la documentation complète : `/docs/DEPLOYMENT_OVH_PERFORMANCE.md`
3. Vérifiez l'état des services : `docker ps`