# Django Backend Deployment on Digital Ocean

## Overview
Your Django backend is now ready for deployment on Digital Ocean. All configuration files and scripts have been prepared.

## Files Created/Modified

### Production Configuration
- ✅ `settings.py` - Updated with production security settings
- ✅ `requirements.txt` - Added production dependencies
- ✅ `.env.production` - Production environment variables (update before deployment)

### Deployment Files
- ✅ `Procfile` - Process configuration for container deployment
- ✅ `gunicorn.conf.py` - Gunicorn server configuration
- ✅ `nginx.conf` - Nginx reverse proxy configuration
- ✅ `Dockerfile` - Docker container configuration
- ✅ `docker-compose.yml` - Multi-container setup
- ✅ `.dockerignore` - Docker build exclusions
- ✅ `deploy.sh` - Automated deployment script

## Pre-Deployment Checklist

### 1. Environment Variables
Update `.env.production` with your actual values:
```bash
# Update these values
ALLOWED_HOSTS=your-domain.com,api.your-domain.com,your-ip-address
DB_NAME=your_db_name
DB_USER=your_db_user  
DB_PASSWORD=your_secure_password
DB_HOST=your_db_host
```

### 2. Domain Configuration
Update `nginx.conf` with your actual domain name:
- Replace `your-domain.com` with your actual domain
- Update SSL certificate paths

### 3. Security Keys
Ensure all secret keys are properly set in `.env.production`:
- `SECRET_KEY` - Django secret key
- `ID_ENCRYPTION_KEY` - For ID protection
- `ID_HASH_SALT` - For hashing

## Deployment Options

### Option 1: Digital Ocean App Platform (Recommended)
1. Connect your GitHub repository to Digital Ocean App Platform
2. Use the `Procfile` for automatic detection
3. Set environment variables in the DO control panel
4. Enable managed database (PostgreSQL) and Redis

### Option 2: Digital Ocean Droplet
1. Create a Ubuntu droplet (minimum 2GB RAM)
2. Upload your code to the droplet
3. Run the deployment script:
```bash
sudo ./deploy.sh
```
4. Follow the post-deployment steps

### Option 3: Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build -d
```

## Post-Deployment Steps

1. **Database Migration**
```bash
python manage.py migrate
```

2. **Create Superuser**
```bash
python manage.py createsuperuser
```

3. **Collect Static Files**
```bash
python manage.py collectstatic --noinput
```

4. **SSL Certificate (for droplet deployment)**
```bash
certbot --nginx -d yourdomain.com
```

5. **Test the API**
- Visit `https://yourdomain.com/admin/` for admin panel
- Test API endpoints

## Monitoring and Maintenance

### Log Files (Droplet deployment)
- Application logs: `/var/log/supervisor/digitalboda.log`
- Celery logs: `/var/log/supervisor/digitalboda_celery.log`
- Nginx logs: `/var/log/nginx/access.log` and `/var/log/nginx/error.log`

### Service Management (Droplet)
```bash
# Restart services
sudo supervisorctl restart all
sudo systemctl reload nginx

# Check service status
sudo supervisorctl status
sudo systemctl status nginx
```

### Database Backup
```bash
pg_dump digitalboda_prod > backup.sql
```

## Security Notes

- 🔒 All sensitive data is environment-variable based
- 🔒 HTTPS redirect enabled in production
- 🔒 Security headers configured
- 🔒 Database SSL required in production
- 🔒 File upload size limits set
- 🔒 CORS properly configured

## Support

If you encounter issues:
1. Check the log files
2. Verify environment variables
3. Ensure database connections are working
4. Test with `python manage.py check --deploy`

Your Django backend is production-ready! 🚀