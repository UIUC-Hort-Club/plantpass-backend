domain_name     = "hortclubplantpass.org"
alternate_names = ["www.hortclubplantpass.org"]

# Email configuration
sender_email          = "noreply@hortclubplantpass.org"
uiuc_hort_club_email  = "hortclubuiuc@gmail.com"
email_lambda_zip_path = "emailhandler_lambda_package.zip"

# Lambda packages, built into this folder by scripts/package.py, and the two
# layer zips built by the deploy workflow.
transaction_lambda_zip_path      = "transactions_handler_lambda_package.zip"
admin_lambda_zip_path            = "admin_password_lambda_package.zip"
products_lambda_zip_path         = "products_handler_lambda_package.zip"
discounts_lambda_zip_path        = "discounts_handler_lambda_package.zip"
payment_methods_lambda_zip_path  = "payment_methods_handler_lambda_package.zip"
websocket_lambda_zip_path        = "websocket_handler_lambda_package.zip"
lock_lambda_zip_path             = "lockhandler_lambda_package.zip"
feature_toggles_lambda_zip_path  = "featuretoggleshandler_lambda_package.zip"
plantpass_access_lambda_zip_path = "plantpassaccess_lambda_package.zip"
auth_layer_zip_path              = "auth_layer.zip"
shared_utils_layer_zip_path      = "shared_utils_layer.zip"
