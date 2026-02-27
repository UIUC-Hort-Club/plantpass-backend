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
│   ├── AdminPassword/         # Admin authentication
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

### Install Dependencies

```bash
cd lambda
pip install -r requirements-test.txt
```

### Run Tests

```bash
cd lambda
pytest

# Run specific tests
pytest tests/test_products_handler.py -v

# Generate coverage report
pytest --cov --cov-report=html
```

### Local Testing

Lambda functions can be tested locally using the test suite. For integration testing with AWS services, use the AWS SAM CLI or deploy to a development environment.

## Lambda Functions

### TransactionHandler
- `POST /transactions` - Create new transaction
- `GET /transactions/{id}` - Read transaction
- `PUT /transactions/{id}` - Update transaction
- `DELETE /transactions/{id}` - Delete transaction
- `GET /transactions` - List all transactions

### ProductsHandler
- `GET /products` - List all products
- `PUT /products` - Update product list

### DiscountsHandler
- `GET /discounts` - List all discounts
- `PUT /discounts` - Update discount list

### PaymentMethodsHandler
- `GET /payment-methods` - List payment methods
- `PUT /payment-methods` - Update payment methods

### AdminPassword
- `POST /admin/login` - Admin authentication
- `POST /admin/password` - Update password
- `POST /admin/reset-request` - Request password reset
- `POST /admin/reset-verify` - Verify reset token

### FeatureTogglesHandler
- `GET /feature-toggles` - Get feature toggles
- `PUT /feature-toggles` - Update feature toggles

### PlantPassAccessHandler
- `GET /plantpass-access` - Get access passphrase
- `PUT /plantpass-access` - Update passphrase
- `POST /plantpass-access/verify` - Verify passphrase

### LockHandler
- `POST /locks/{resource}` - Acquire lock
- `DELETE /locks/{resource}` - Release lock
- `GET /locks/{resource}` - Check lock status

### WebSocketHandler
- `$connect` - WebSocket connection
- `$disconnect` - WebSocket disconnection
- `$default` - Default message handler

### EmailHandler
- Sends password reset emails via SES

## Infrastructure

### Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Required Terraform Variables

Create a `terraform.tfvars` file:

```hcl
reset_token_hash = "your-reset-token-hash"
sender_email = "noreply@yourdomain.com"
uiuc_hort_club_email = "admin@yourdomain.com"
```

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

Lambda functions use environment variables for configuration:

- `TRANSACTIONS_TABLE` - DynamoDB transactions table
- `PRODUCTS_TABLE` - DynamoDB products table
- `DISCOUNTS_TABLE` - DynamoDB discounts table
- `PAYMENT_METHODS_TABLE` - DynamoDB payment methods table
- `ADMIN_PASSWORD_TABLE` - DynamoDB admin passwords table
- `FEATURE_TOGGLES_TABLE` - DynamoDB feature toggles table
- `PLANTPASS_ACCESS_TABLE` - DynamoDB access control table
- `LOCKS_TABLE` - DynamoDB locks table
- `WEBSOCKET_TABLE` - DynamoDB WebSocket connections table
- `SENDER_EMAIL` - SES sender email address
- `RESET_TOKEN_HASH` - Password reset token hash

## Frontend Repository

This backend serves the PlantPass frontend application. See the [plantpass-frontend](https://github.com/your-org/plantpass-frontend) repository for the React application.

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
