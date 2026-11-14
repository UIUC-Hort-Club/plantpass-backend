# PlantPass Backend

Backend infrastructure and Lambda functions for the PlantPass point-of-sale application.

## Architecture

- **Backend**: Python AWS Lambda functions
- **API**: AWS API Gateway (REST + WebSocket)
- **Database**: Amazon DynamoDB
- **Infrastructure**: Terraform
- **CI/CD**: GitHub Actions
- **Email**: Amazon SES

## Features

- Transaction management (CRUD operations)
- Product and discount management
- Payment method configuration
- Admin authentication and password reset
- Feature toggles for runtime configuration
- Resource locking for concurrent edit prevention
- Real-time updates via WebSocket
- Email delivery for password resets

## Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate credentials
- Terraform 1.6+
- Docker (for building Lambda layers)

## Project Structure

```
plantpass-backend/
├── lambda/                    # Lambda function code
│   ├── TransactionHandler/    # Transaction CRUD operations
│   ├── ProductsHandler/       # Product management
│   ├── DiscountsHandler/      # Discount management
│   ├── PaymentMethodsHandler/ # Payment method management
│   ├── AdminAuthHandler/      # Admin authentication
│   ├── PlantPassAccessHandler/# Staff access control
│   ├── FeatureTogglesHandler/ # Feature toggle management
│   ├── LockHandler/           # Resource locking
│   ├── WebSocketHandler/      # Real-time updates
│   ├── EmailHandler/          # Email delivery
│   ├── shared/                # Shared utilities
│   ├── layers/                # Lambda layers
│   └── tests/                 # Backend tests
└── terraform/                 # Infrastructure as code
    ├── lambda.tf              # Lambda function definitions
    ├── apigateway.tf          # API Gateway configuration
    ├── dynamodb.tf            # DynamoDB tables
    ├── s3.tf                  # S3 buckets
    ├── cloudfront.tf          # CloudFront distribution
    ├── route53.tf             # DNS configuration
    ├── ses.tf                 # Email service
    └── variables.tf           # Terraform variables
```

## Development

```bash
make check     # creates .venv, runs pytest, terraform fmt and terraform validate
make test      # pytest only
make help      # everything else
```

Working with an AI agent, or new to the codebase: start with `AGENTS.md`, then
`docs/PRODUCT.md` and `docs/ARCHITECTURE.md`. What is planned and what was
declined is in `docs/ROADMAP.md`.

### Local Testing

The test suite mocks AWS. There is no local or staging environment yet: nothing short of production runs a Lambda against DynamoDB. See `docs/ROADMAP.md`, item R5.

## API routes

`terraform/apigateway.tf` is the source of truth for routes, and
`docs/ARCHITECTURE.md` has the table of routes, which Lambda serves each, and
who may call it.

## Infrastructure

### Terraform variables

Declared in `terraform/variables.tf`; the non-secret values are in
`terraform/terraform.tfvars`. The Lambda zip paths are passed by the deploy
workflow. Do not apply from a laptop: merging to `main` deploys.

### AWS Resources Created

- Lambda functions (10+)
- API Gateway (REST + WebSocket)
- DynamoDB tables (8+)
- S3 bucket for frontend hosting
- CloudFront distribution
- Route53 DNS records
- ACM SSL certificate
- SES email configuration
- Lambda layers for dependencies

## CI/CD

Deployment is automated via GitHub Actions:

1. **Test**: Run Python tests with pytest
2. **Build**: Package Lambda functions and layers
3. **Deploy**: Apply Terraform configuration
4. **Verify**: Check deployment health

See `.github/workflows/deploy-backend.yaml` for details.

## Environment Variables

Each Lambda's environment is set in `terraform/lambda.tf`. Read it there; the
names differ between handlers.

## Frontend Repository

This backend serves the PlantPass frontend application. See the [plantpass-frontend](https://github.com/UIUC-Hort-Club/plantpass-frontend) repository for the React application.

## Security

- Admin authentication with bcrypt password hashing
- JWT tokens for session management
- Resource locking to prevent concurrent modifications
- Passphrase protection for staff access
- CORS configuration for API security
- Environment-based secrets management

## Contributing

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `pytest`
4. Update Terraform if infrastructure changes
5. Submit a pull request

## License

Proprietary - All rights reserved

## Contact

Joseph (Joe) Ku  
Email: josephku825@gmail.com
