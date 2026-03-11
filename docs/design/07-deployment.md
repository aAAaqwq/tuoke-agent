# 拓客Agent - 部署方案

> **文档版本**: V1.0  
> **设计日期**: 2026-03-10  
> **设计人**: 小ops (运维专家)  
> **状态**: 初稿完成

---

## 1. 部署方案总览

### 1.1 部署阶段规划

| 阶段 | 时间 | 目标 | 部署方式 | 预算/月 |
|------|------|------|----------|---------|
| **MVP 阶段** | 1-2月 | 验证产品 | Vercel + Railway + Supabase | $100-300 |
| **成长阶段** | 3-6月 | 稳定运行 | 阿里云 ECS + RDS | ¥2,000-5,000 |
| **规模阶段** | 6月+ | 高可用扩展 | K8s 集群 + 多地域 | ¥10,000+ |

### 1.2 架构演进路线

```
┌─────────────────────────────────────────────────────────────────────┐
│                         部署架构演进                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Phase 1: MVP (PaaS 托管)                                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐               │
│  │ Vercel  │  │ Railway │  │Supabase │  │ Upstash │               │
│  │ 前端    │  │ 后端API │  │ 数据库  │  │ Redis   │               │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘               │
│  成本: ~$100/月                                                     │
│                                                                     │
│  Phase 2: 自托管 (单机/小集群)                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    阿里云 ECS / 腾讯云 CVM                    │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │   │
│  │  │ Docker │ │ Docker │ │ Docker │ │ Docker │ │ Docker │    │   │
│  │  │ Nginx  │ │ API    │ │ Celery │ │OpenClaw│ │ Redis  │    │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    云数据库 RDS PostgreSQL                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  成本: ¥2,000-5,000/月                                              │
│                                                                     │
│  Phase 3: K8s 集群 (高可用)                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Kubernetes Cluster                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │ API Pool │ │Worker Pool│ │Agent Pool│ │ Gateway  │       │   │
│  │  │ (3 nodes)│ │ (5 nodes)│ │ (3 nodes)│ │ (2 nodes)│       │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  成本: ¥10,000+/月                                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 服务器选型方案

### 2.1 云服务商对比

| 服务商 | 优势 | 劣势 | 推荐场景 |
|--------|------|------|----------|
| **阿里云** | 国内市场份额最大，生态完善，技术支持好 | 价格略高，账单复杂 | 国内业务首选 |
| **腾讯云** | 价格竞争力强，微信生态集成好 | 企业级服务略弱 | 中小企业、微信场景 |
| **华为云** | 政企客户首选，安全合规强 | 生态不如阿里/腾讯 | 政府、金融、国企 |
| **AWS** | 全球覆盖，服务最全面 | 国内访问需备案，价格高 | 出海业务 |
| **Vercel** | 前端部署体验最佳，Edge Network | 后端支持有限 | 前端/全栈 MVP |
| **Railway** | 开发者体验好，定价透明 | 国内访问较慢 | 后端 MVP |

### 2.2 MVP 阶段配置

#### 方案 A: 全托管 PaaS（推荐）

```yaml
# MVP 阶段 - 全托管方案
服务列表:
  前端:
    服务商: Vercel
    套餐: Pro ($20/月)
    配置: 自动扩缩容，边缘缓存
    
  后端:
    服务商: Railway
    套餐: Pro ($20/月)
    配置: 2 vCPU, 4GB RAM, 自动扩容
    
  数据库:
    服务商: Supabase
    套餐: Pro ($25/月)
    配置: 8GB 数据库, pgvector 支持
    
  Redis:
    服务商: Upstash
    套餐: Pay-as-you-go
    预估: $10/月
    
  OpenClaw:
    服务商: Railway (独立服务)
    套餐: $10/月
    配置: 1 vCPU, 2GB RAM

总计: ~$85/月 (不含 LLM API)
```

#### 方案 B: 混合部署（成本优化）

```yaml
# MVP 阶段 - 混合方案
服务列表:
  前端:
    服务商: Vercel
    套餐: Free
    说明: 免费版足够 MVP 使用
    
  后端 + OpenClaw:
    服务商: 阿里云 ECS
    规格: ecs.c6.large (2 vCPU, 4GB)
    价格: ¥200/月
    
  数据库:
    服务商: 阿里云 RDS PostgreSQL
    规格: pg.n4.small.1 (1 vCPU, 2GB)
    价格: ¥300/月
    存储: 20GB SSD
    
  Redis:
    服务商: 阿里云 Redis
    规格: redis.master.small.default
    价格: ¥150/月

总计: ~¥650/月 (约 $90)
```

### 2.3 成长阶段配置

```yaml
# 成长阶段 - 阿里云方案
架构:
  负载均衡:
    服务: SLB
    规格: slb.s1.small
    价格: ¥50/月
    
  应用服务器:
    服务: ECS
    规格: ecs.c6.xlarge (4 vCPU, 8GB) x 2
    价格: ¥800/月 x 2 = ¥1,600/月
    
  数据库:
    服务: RDS PostgreSQL
    规格: pg.n4.medium.1 (2 vCPU, 4GB)
    价格: ¥600/月
    存储: 100GB SSD = ¥100/月
    主从: 高可用版 +¥300/月
    
  Redis:
    服务: Redis
    规格: redis.master.mid.default (2GB)
    价格: ¥350/月
    
  OSS:
    服务: 对象存储
    存储: 100GB
    价格: ¥15/月
    
  带宽:
    服务: EIP
    带宽: 10Mbps
    价格: ¥300/月

总计: ~¥3,300/月
```

### 2.4 自有服务器评估

| 场景 | 推荐度 | 说明 |
|------|--------|------|
| **家里/办公室服务器** | ⭐⭐ | 需公网IP，稳定性差，运维成本高 |
| **托管机房** | ⭐⭐⭐ | 适合长期稳定业务，初始投入大 |
| **边缘节点（Jetson/NAS）** | ⭐ | 仅适合开发测试，性能不足 |

**结论**：建议 MVP 阶段使用云服务，规模化后考虑混合云/自建机房。

---

## 3. Docker/K8s 容器化方案

### 3.1 Docker Compose（MVP 阶段）

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ==================== 基础设施 ====================
  
  # 反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - api
      - web
    networks:
      - frontend
      - backend
    restart: always
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ==================== 前端服务 ====================
  
  # Next.js 应用
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
      args:
        - NEXT_PUBLIC_API_URL=${API_URL}
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=${API_URL}
    networks:
      - frontend
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ==================== 后端服务 ====================
  
  # FastAPI 主服务
  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://tuoke:${DB_PASSWORD}@postgres:5432/tuoke
      - REDIS_URL=redis://redis:6379/0
      - OPENCLAW_URL=http://openclaw:3000
      - JWT_SECRET=${JWT_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - backend
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  # Celery Worker
  celery-worker:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    command: celery -A app.tasks worker -l info -c 4 -Q collect,reach,analyze,default
    environment:
      - DATABASE_URL=postgresql://tuoke:${DB_PASSWORD}@postgres:5432/tuoke
      - REDIS_URL=redis://redis:6379/0
      - OPENCLAW_URL=http://openclaw:3000
    depends_on:
      - postgres
      - redis
    networks:
      - backend
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 2G

  # Celery Beat (定时任务)
  celery-beat:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    command: celery -A app.tasks beat -l info --scheduler django-celery-beat:DatabaseScheduler
    environment:
      - DATABASE_URL=postgresql://tuoke:${DB_PASSWORD}@postgres:5432/tuoke
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - backend
    restart: always

  # ==================== AI Agent 服务 ====================
  
  # OpenClaw Gateway
  openclaw:
    image: openclaw/openclaw:latest
    ports:
      - "3000:3000"
    volumes:
      - ./openclaw-config:/root/.openclaw
      - openclaw-data:/root/.openclaw-data
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=info
    networks:
      - backend
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  # ==================== 数据存储 ====================
  
  # PostgreSQL + pgvector
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=tuoke
      - POSTGRES_USER=tuoke
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-db:/docker-entrypoint-initdb.d
    networks:
      - backend
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tuoke -d tuoke"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - backend
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MinIO (文件存储)
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
    volumes:
      - minio-data:/data
    command: server /data --console-address ":9001"
    networks:
      - backend
    restart: always

  # ==================== 监控服务 ====================
  
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    networks:
      - monitoring
    restart: always

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    networks:
      - monitoring
    restart: always

networks:
  frontend:
  backend:
  monitoring:

volumes:
  postgres-data:
  redis-data:
  minio-data:
  openclaw-data:
  prometheus-data:
  grafana-data:
```

### 3.2 Dockerfile 示例

```dockerfile
# apps/api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd -m -u 1000 tuoke && chown -R tuoke:tuoke /app
USER tuoke

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# apps/web/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# 安装依赖
COPY package.json package-lock.json ./
RUN npm ci

# 构建应用
COPY . .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# 生产镜像
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 复制构建产物
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

### 3.3 Kubernetes 部署（规模阶段）

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tuoke
  labels:
    app: tuoke-agent

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tuoke-config
  namespace: tuoke
data:
  NODE_ENV: "production"
  LOG_LEVEL: "info"
  DATABASE_HOST: "postgres-service"
  REDIS_HOST: "redis-service"
  OPENCLAW_URL: "http://openclaw-service:3000"

---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: tuoke-secrets
  namespace: tuoke
type: Opaque
stringData:
  DATABASE_URL: "postgresql://tuoke:$(DB_PASSWORD)@postgres-service:5432/tuoke"
  REDIS_URL: "redis://redis-service:6379/0"
  JWT_SECRET: "$(JWT_SECRET)"
  OPENAI_API_KEY: "$(OPENAI_API_KEY)"
  ANTHROPIC_API_KEY: "$(ANTHROPIC_API_KEY)"

---
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tuoke-api
  namespace: tuoke
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tuoke-api
  template:
    metadata:
      labels:
        app: tuoke-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
    spec:
      containers:
      - name: api
        image: tuoke/api:v1.0.0
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: tuoke-config
        - secretRef:
            name: tuoke-secrets
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: tuoke-api-service
  namespace: tuoke
spec:
  selector:
    app: tuoke-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/celery-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tuoke-celery-worker
  namespace: tuoke
spec:
  replicas: 4
  selector:
    matchLabels:
      app: tuoke-celery-worker
  template:
    metadata:
      labels:
        app: tuoke-celery-worker
    spec:
      containers:
      - name: worker
        image: tuoke/api:v1.0.0
        command: ["celery", "-A", "app.tasks", "worker", "-l", "info", "-c", "8"]
        envFrom:
        - configMapRef:
            name: tuoke-config
        - secretRef:
            name: tuoke-secrets
        resources:
          requests:
            cpu: 1000m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 2Gi

---
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: tuoke-celery-hpa
  namespace: tuoke
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: tuoke-celery-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: External
    external:
      metric:
        name: celery_queue_length
      target:
        type: AverageValue
        averageValue: 100
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tuoke-ingress
  namespace: tuoke
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - api.tuoke-agent.com
    - app.tuoke-agent.com
    secretName: tuoke-tls
  rules:
  - host: api.tuoke-agent.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: tuoke-api-service
            port:
              number: 80
  - host: app.tuoke-agent.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: tuoke-web-service
            port:
              number: 80
```

---

## 4. CI/CD 流水线方案

### 4.1 GitHub Actions 工作流

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_API: ghcr.io/${{ github.repository }}/api
  IMAGE_WEB: ghcr.io/${{ github.repository }}/web

jobs:
  # ==================== 测试阶段 ====================
  
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install poetry
          cd apps/api && poetry install
      
      - name: Run linting
        run: |
          cd apps/api
          poetry run ruff check .
          poetry run mypy .

  test-api:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: test_tuoke
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install poetry
          cd apps/api && poetry install
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_tuoke
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd apps/api
          poetry run pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./apps/api/coverage.xml

  test-web:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: apps/web/package-lock.json
      
      - name: Install dependencies
        run: cd apps/web && npm ci
      
      - name: Run tests
        run: cd apps/web && npm test
      
      - name: Build
        run: cd apps/web && npm run build

  # ==================== 构建阶段 ====================
  
  build-api:
    runs-on: ubuntu-latest
    needs: [test-api]
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.IMAGE_API }}
          tags: |
            type=ref,event=branch
            type=sha,prefix=
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./apps/api
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  build-web:
    runs-on: ubuntu-latest
    needs: [test-web]
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.IMAGE_WEB }}
          tags: |
            type=ref,event=branch
            type=sha,prefix=
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./apps/web
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            NEXT_PUBLIC_API_URL=${{ secrets.API_URL }}

  # ==================== 部署阶段 ====================
  
  deploy-staging:
    runs-on: ubuntu-latest
    needs: [build-api, build-web]
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Staging
        run: |
          echo "Deploying to staging environment..."
          # SSH 到服务器执行部署脚本
          # 或使用 kubectl apply
      
      - name: Run smoke tests
        run: |
          echo "Running smoke tests..."
          curl -f https://staging.tuoke-agent.com/health || exit 1

  deploy-production:
    runs-on: ubuntu-latest
    needs: [build-api, build-web]
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Production
        run: |
          echo "Deploying to production environment..."
          # 滚动更新策略
      
      - name: Notify on success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: success
          fields: repo,message,commit,author
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### 4.2 部署脚本

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=$1
VERSION=$2

if [ -z "$ENVIRONMENT" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <environment> <version>"
    exit 1
fi

echo "🚀 Deploying version $VERSION to $ENVIRONMENT..."

# 拉取最新镜像
docker pull ghcr.io/tuoke/api:$VERSION
docker pull ghcr.io/tuoke/web:$VERSION

# 滚动更新
docker-compose -f docker-compose.$ENVIRONMENT.yml up -d --no-deps --build api celery-worker

# 健康检查
echo "⏳ Waiting for health check..."
sleep 30

# 验证部署
curl -f https://$ENVIRONMENT.tuoke-agent.com/health || {
    echo "❌ Health check failed, rolling back..."
    docker-compose -f docker-compose.$ENVIRONMENT.yml rollback
    exit 1
}

echo "✅ Deployment successful!"
```

---

## 5. 监控告警方案

### 5.1 监控架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          监控架构                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ 应用指标      │  │ 系统指标     │  │ 业务指标     │             │
│  │ (Prometheus) │  │ (Node Export)│  │ (自定义)     │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                 │                      │
│         └────────────────┬┴─────────────────┘                      │
│                          │                                         │
│                          ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                     Prometheus                                │ │
│  │            (指标采集 + 存储 + 告警规则)                        │ │
│  └──────────────────────────┬───────────────────────────────────┘ │
│                             │                                      │
│              ┌──────────────┼──────────────┐                      │
│              ▼              ▼              ▼                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │
│  │   Grafana    │ │ AlertManager │ │  Langfuse    │              │
│  │   (可视化)   │ │   (告警)     │ │ (LLM 可观测) │              │
│  └──────────────┘ └──────────────┘ └──────────────┘              │
│                             │                                      │
│                             ▼                                      │
│              ┌──────────────────────────┐                         │
│              │      通知渠道            │                         │
│              │ Slack / 邮件 / 企微      │                         │
│              └──────────────────────────┘                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Prometheus 配置

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'tuoke-prod'
    environment: 'production'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - /etc/prometheus/rules/*.yml

scrape_configs:
  # API 服务
  - job_name: 'tuoke-api'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - tuoke
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: tuoke-api
        action: keep
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        regex: "true"
        action: keep
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
        regex: "(.+)"
        target_label: __address__
        replacement: "${1}"

  # Celery Workers
  - job_name: 'celery-workers'
    static_configs:
      - targets: ['celery-exporter:9808']

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node Exporter (系统指标)
  - job_name: 'node'
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - source_labels: [__address__]
        regex: '(.*):10250'
        replacement: '${1}:9100'
        target_label: __address__

  # OpenClaw
  - job_name: 'openclaw'
    static_configs:
      - targets: ['openclaw:3000']
    metrics_path: /metrics
```

### 5.3 告警规则

```yaml
# prometheus/rules/tuoke-alerts.yml
groups:
  - name: tuoke-api-alerts
    rules:
      # API 响应时间告警
      - alert: HighAPILatency
        expr: |
          histogram_quantile(0.95, 
            rate(http_request_duration_seconds_bucket{job="tuoke-api"}[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "API 响应时间过高"
          description: "95分位响应时间超过 2 秒，当前值: {{ $value }}s"

      # API 错误率告警
      - alert: HighAPIErrorRate
        expr: |
          rate(http_requests_total{job="tuoke-api", status=~"5.."}[5m]) 
          / rate(http_requests_total{job="tuoke-api"}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "API 错误率过高"
          description: "5xx 错误率超过 5%，当前值: {{ $value | humanizePercentage }}"

      # Celery 队列积压告警
      - alert: CeleryQueueBacklog
        expr: celery_queue_length{queue="reach"} > 500
        for: 10m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "Celery 队列积压"
          description: "触达队列积压超过 500，当前值: {{ $value }}"

      # Celery Worker 宕机告警
      - alert: CeleryWorkersDown
        expr: celery_workers_online < 2
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "Celery Workers 数量不足"
          description: "在线 Worker 少于 2 个，当前值: {{ $value }}"

  - name: tuoke-agent-alerts
    rules:
      # Agent 任务失败率告警
      - alert: HighAgentFailureRate
        expr: |
          rate(agent_tasks_total{status="failed"}[15m]) 
          / rate(agent_tasks_total[15m]) > 0.1
        for: 10m
        labels:
          severity: critical
          team: ai
        annotations:
          summary: "Agent 任务失败率过高"
          description: "Agent 任务失败率超过 10%，当前值: {{ $value | humanizePercentage }}"

      # LLM 成本异常告警
      - alert: HighLLMCost
        expr: rate(agent_llm_cost_dollars[1h]) > 20
        for: 30m
        labels:
          severity: warning
          team: ai
        annotations:
          summary: "LLM 成本异常增长"
          description: "LLM 小时成本超过 $20，当前值: ${{ $value }}"

      # LLM Token 使用量告警
      - alert: HighTokenUsage
        expr: rate(agent_llm_tokens_total[1h]) > 1000000
        for: 1h
        labels:
          severity: warning
          team: ai
        annotations:
          summary: "LLM Token 使用量过高"
          description: "小时 Token 使用超过 100 万，当前值: {{ $value }}"

  - name: tuoke-infrastructure-alerts
    rules:
      # 数据库连接数告警
      - alert: HighDatabaseConnections
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
          team: dba
        annotations:
          summary: "数据库连接数过高"
          description: "PostgreSQL 连接数超过 80，当前值: {{ $value }}"

      # 数据库磁盘空间告警
      - alert: DatabaseDiskSpaceLow
        expr: |
          (pg_database_size_bytes / pg_database_size_bytes{datname="tuoke"} * 100) < 20
        for: 10m
        labels:
          severity: critical
          team: dba
        annotations:
          summary: "数据库磁盘空间不足"
          description: "数据库剩余空间低于 20%"

      # Redis 内存告警
      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.8
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "Redis 内存使用率过高"
          description: "Redis 内存使用率超过 80%"

      # 节点 CPU 告警
      - alert: NodeCPUHigh
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
        for: 10m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "节点 CPU 使用率过高"
          description: "节点 {{ $labels.instance }} CPU 使用率超过 85%"

      # 节点内存告警
      - alert: NodeMemoryHigh
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
        for: 10m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "节点内存使用率过高"
          description: "节点 {{ $labels.instance }} 内存使用率超过 90%"

  - name: tuoke-business-alerts
    rules:
      # 邮件送达率告警
      - alert: LowEmailDeliveryRate
        expr: |
          rate(tuoke_emails_delivered_total[1h]) 
          / rate(tuoke_emails_sent_total[1h]) < 0.9
        for: 30m
        labels:
          severity: warning
          team: business
        annotations:
          summary: "邮件送达率过低"
          description: "邮件送达率低于 90%，当前值: {{ $value | humanizePercentage }}"

      # 线索采集量异常
      - alert: LowProspectCollection
        expr: rate(tuoke_prospects_collected_total[1h]) < 10
        for: 2h
        labels:
          severity: info
          team: business
        annotations:
          summary: "线索采集量异常低"
          description: "小时采集线索数低于 10，可能有数据源问题"
```

### 5.4 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "拓客Agent 监控面板",
    "panels": [
      {
        "title": "API 请求速率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{job=\"tuoke-api\"}[5m])",
            "legendFormat": "{{method}} {{path}}"
          }
        ]
      },
      {
        "title": "API 响应时间 (P95)",
        "type": "stat",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ],
        "thresholds": {
          "mode": "absolute",
          "steps": [
            {"color": "green", "value": null},
            {"color": "yellow", "value": 1},
            {"color": "red", "value": 2}
          ]
        }
      },
      {
        "title": "Celery 队列长度",
        "type": "graph",
        "targets": [
          {
            "expr": "celery_queue_length{queue=\"collect\"}",
            "legendFormat": "采集队列"
          },
          {
            "expr": "celery_queue_length{queue=\"reach\"}",
            "legendFormat": "触达队列"
          },
          {
            "expr": "celery_queue_length{queue=\"analyze\"}",
            "legendFormat": "分析队列"
          }
        ]
      },
      {
        "title": "Agent 任务状态",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (status) (agent_tasks_total)",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "LLM 成本趋势",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(agent_llm_cost_dollars[1h]) * 24 * 30",
            "legendFormat": "预估月成本"
          }
        ]
      },
      {
        "title": "业务指标",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(tuoke_prospects_total)",
            "legendFormat": "总线索数"
          },
          {
            "expr": "sum(tuoke_reaches_total)",
            "legendFormat": "总触达数"
          },
          {
            "expr": "avg(tuoke_email_open_rate)",
            "legendFormat": "平均打开率"
          }
        ]
      }
    ]
  }
}
```

### 5.5 告警通知配置

```yaml
# alertmanager/config.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/xxx'

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default-receiver'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      continue: true
    
    - match:
        team: ai
      receiver: 'ai-team'
    
    - match:
        team: business
      receiver: 'business-team'

receivers:
  - name: 'default-receiver'
    slack_configs:
      - channel: '#tuoke-alerts'
        send_resolved: true
        title: '{{ .Status | toUpper }}: {{ .GroupLabels.alertname }}'
        text: >-
          {{ range .Alerts }}
          *Alert:* {{ .Labels.alertname }}
          *Severity:* {{ .Labels.severity }}
          *Description:* {{ .Annotations.description }}
          *Details:* {{ .Annotations.summary }}
          {{ end }}

  - name: 'critical-alerts'
    slack_configs:
      - channel: '#tuoke-critical'
        send_resolved: true
    webhook_configs:
      - url: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx'
        send_resolved: true

  - name: 'ai-team'
    slack_configs:
      - channel: '#tuoke-ai'
        send_resolved: true

  - name: 'business-team'
    slack_configs:
      - channel: '#tuoke-business'
        send_resolved: true
```

---

## 6. 成本估算

### 6.1 MVP 阶段成本（月度）

```yaml
# MVP 阶段成本估算
基础设施:
  Vercel Pro: $20
  Railway Pro: $20
  Supabase Pro: $25
  Upstash Redis: $10
  域名 + SSL: $2
  小计: $77/月

LLM API:
  OpenAI GPT-4o-mini:
    用量: 100万 tokens/月
    价格: $0.15/1M input, $0.60/1M output
    预估: $50/月
  
  OpenAI GPT-4o (复杂任务):
    用量: 10万 tokens/月
    价格: $2.5/1M input, $10/1M output
    预估: $30/月
  
  Claude 3.5 Sonnet:
    用量: 5万 tokens/月
    价格: $3/1M input, $15/1M output
    预估: $20/月
  
  小计: $100/月

数据源 API:
  企查查:
    用量: 3000次/月
    价格: ¥0.03/次
    预估: ¥90 ($12)
  
  天眼查:
    用量: 2000次/月
    价格: ¥0.04/次
    预估: ¥80 ($11)
  
  小计: $23/月

邮件服务:
  Resend:
    用量: 5000封/月
    价格: 免费 tier
    预估: $0

监控告警:
  Langfuse (自托管): $0
  Grafana Cloud Free: $0
  小计: $0

总计:
  基础设施: $77
  LLM API: $100
  数据源: $23
  总计: ~$200/月
```

### 6.2 成长阶段成本（月度）

```yaml
# 成长阶段成本估算 (1000 活跃用户)
基础设施:
  阿里云 ECS (2台):
    ecs.c6.xlarge (4 vCPU, 8GB) x 2
    价格: ¥800 x 2 = ¥1,600/月
  
  阿里云 RDS PostgreSQL:
    pg.n4.medium.1 (2 vCPU, 4GB) 高可用版
    价格: ¥900/月
    存储: 100GB SSD = ¥100/月
  
  阿里云 Redis:
    redis.master.mid.default (2GB)
    价格: ¥350/月
  
  阿里云 SLB:
    slb.s1.small
    价格: ¥50/月
  
  阿里云 OSS:
    200GB 存储
    价格: ¥30/月
  
  阿里云 EIP:
    10Mbps 带宽
    价格: ¥300/月
  
  小计: ¥3,330/月 (~$460)

LLM API:
  OpenAI GPT-4o-mini:
    用量: 1000万 tokens/月
    预估: $500/月
  
  OpenAI GPT-4o:
    用量: 100万 tokens/月
    预估: $300/月
  
  Claude 3.5 Sonnet:
    用量: 50万 tokens/月
    预估: $200/月
  
  DeepSeek V3 (中文优化):
    用量: 500万 tokens/月
    价格: $0.1/1M tokens
    预估: $50/月
  
  小计: $1,050/月

数据源 API:
  企查查:
    用量: 30000次/月
    预估: ¥900 ($125)
  
  天眼查:
    用量: 20000次/月
    预估: ¥800 ($110)
  
  Apollo.io (海外数据):
    Basic Plan: $49/月
  
  小计: $284/月

邮件服务:
  SendGrid Pro:
    用量: 10万封/月
    价格: $89/月

监控告警:
  Grafana Cloud: $49/月
  Langfuse Cloud: $29/月
  小计: $78/月

总计:
  基础设施: $460
  LLM API: $1,050
  数据源: $284
  邮件服务: $89
  监控: $78
  总计: ~$1,960/月 (¥14,000)
```

### 6.3 成本优化策略

```yaml
# 成本优化建议

LLM 成本优化:
  1. 模型分层:
    - 简单分类: GPT-4o-mini / DeepSeek V3
    - 内容生成: GPT-4o-mini
    - 复杂推理: Claude 3.5 Sonnet / GPT-4o (仅必要时)
  
  2. 缓存策略:
    - 相似查询缓存 (语义相似度)
    - 画像结果缓存 (24小时有效期)
    - 减少重复调用 30-50%
  
  3. Prompt 优化:
    - 精简 Prompt 长度
    - 使用 Few-shot 示例
    - 减少输出 token 数量
  
  4. 本地模型:
    - 部署 Ollama + Qwen2.5 (简单任务)
    - 节省 30-40% LLM 成本

数据源成本优化:
  1. 数据去重:
    - 采集前检查数据库
    - 避免重复付费
  
  2. 批量查询:
    - 合并多个查询请求
    - 利用批量 API 优惠
  
  3. 自建数据库:
    - 定期采集公开数据
    - 减少商业 API 依赖

基础设施成本优化:
  1. 预留实例:
    - 年付享 30-50% 折扣
    - 预估稳定使用量后切换
  
  2. Spot 实例:
    - Worker 节点使用 Spot
    - 节省 60-70% 计算成本
  
  3. 自动扩缩容:
    - 夜间/周末缩减规模
    - 按需付费
```

### 6.4 成本效益分析

```
┌─────────────────────────────────────────────────────────────────────┐
│                       成本效益分析                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  假设场景: 1000 活跃用户/月                                          │
│                                                                     │
│  成本项                    金额                                      │
│  ─────────────────────────────────────────────                      │
│  基础设施                  $460/月                                   │
│  LLM API                  $1,050/月                                  │
│  数据源                    $284/月                                   │
│  邮件服务                    $89/月                                  │
│  监控                        $78/月                                  │
│  ─────────────────────────────────────────────                      │
│  总成本                   $1,961/月                                  │
│                                                                     │
│  收入项 (假设):                                                      │
│  ─────────────────────────────────────────────                      │
│  SaaS 订阅 (1000 x $29)   $29,000/月                                 │
│  成功佣金 (100 x $100)    $10,000/月                                 │
│  ─────────────────────────────────────────────                      │
│  总收入                   $39,000/月                                 │
│                                                                     │
│  毛利率: ($39,000 - $1,961) / $39,000 = 95%                         │
│                                                                     │
│  单用户成本: $1.96/月                                                │
│  单用户收入: $39/月                                                  │
│  成本占比: 5%                                                        │
│                                                                     │
│  结论: 成本结构健康，具备良好的盈利空间                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. 部署检查清单

### 7.1 上线前检查

```markdown
## 部署检查清单

### 基础设施
- [ ] 服务器配置完成
- [ ] 数据库已创建并初始化
- [ ] Redis 已配置
- [ ] SSL 证书已安装
- [ ] 域名解析已配置
- [ ] 防火墙规则已设置

### 应用配置
- [ ] 环境变量已配置
- [ ] API Keys 已设置
- [ ] 数据库连接池已配置
- [ ] 日志收集已启用

### 安全检查
- [ ] 敏感信息已加密存储
- [ ] API 认证已启用
- [ ] 限流规则已配置
- [ ] CORS 已正确配置
- [ ] SQL 注入防护已启用

### 监控告警
- [ ] Prometheus 已部署
- [ ] Grafana Dashboard 已配置
- [ ] 告警规则已设置
- [ ] 通知渠道已测试
- [ ] Langfuse 已配置

### 备份恢复
- [ ] 数据库备份策略已配置
- [ ] 备份恢复测试已通过
- [ ] 灾难恢复计划已制定

### 性能测试
- [ ] 压力测试已通过
- [ ] 并发测试已通过
- [ ] 内存泄漏测试已通过

### 文档
- [ ] 部署文档已更新
- [ ] 运维手册已编写
- [ ] API 文档已发布
```

### 7.2 运维 SOP

```markdown
## 日常运维 SOP

### 每日检查 (5分钟)
1. 检查 Grafana 监控面板
2. 查看错误日志
3. 确认备份完成
4. 检查告警通知

### 每周检查 (30分钟)
1. 审查系统资源使用趋势
2. 检查 LLM API 成本趋势
3. 审查告警规则有效性
4. 更新安全补丁

### 每月检查 (2小时)
1. 容量规划和成本优化
2. 备份恢复演练
3. 安全审计
4. 性能调优

### 应急响应
1. 收到告警后 5 分钟内确认
2. 15 分钟内定位问题
3. 30 分钟内恢复服务 (P1)
4. 事后 24 小时内完成复盘
```

---

## 8. 总结

### 8.1 部署方案总结

| 阶段 | 时间 | 预算 | 关键目标 |
|------|------|------|----------|
| **MVP** | 1-2月 | $200/月 | 快速验证产品 |
| **成长** | 3-6月 | $2,000/月 | 稳定运行、优化成本 |
| **规模** | 6月+ | $10,000+/月 | 高可用、多地域 |

### 8.2 关键决策点

| 决策 | 选项 | 推荐 | 理由 |
|------|------|------|------|
| 云服务商 | 阿里云 vs 腾讯云 | 阿里云 | 生态完善，技术支持好 |
| 容器化 | Docker vs K8s | MVP用Docker，规模化用K8s | 复杂度匹配规模 |
| 数据库 | 自托管 vs 云服务 | 云服务 RDS | 省运维，高可用 |
| LLM | 单一 vs 多供应商 | 多供应商 | 成本优化，容灾 |

### 8.3 下一步行动

- [ ] 确定部署阶段和时间表
- [ ] 申请云服务账号和预算
- [ ] 配置 CI/CD 流水线
- [ ] 搭建监控告警系统
- [ ] 编写运维文档

---

**文档版本**: V1.0  
**完成时间**: 2026-03-10  
**设计人**: 小ops (运维专家)
