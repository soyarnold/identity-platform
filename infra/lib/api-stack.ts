import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";

/**
 * API compute scaffold — future home for:
 * - ECS cluster + Fargate service running apps/api (uvicorn/gunicorn)
 * - Application Load Balancer (HTTPS)
 * - Task env: DATABASE_URL, REDIS_URL, SECRET_KEY, CORS_ORIGINS,
 *   FRONTEND_URL, WEBAUTHN_RP_ID / ORIGINS, cookie settings
 * - Secrets from Secrets Manager / SSM
 *
 * No AWS resources are created yet (phase 09 scaffold only).
 */
export class ApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // TODO(phase-later): ecs.Cluster + FargateService + ApplicationLoadBalancer
    // TODO(phase-later): container image from ECR (CI build of apps/api)
    new cdk.CfnOutput(this, "ApiStatus", {
      value: "scaffold-only",
      description: "Replace with ALB DNS name when ApiStack is implemented",
    });
  }
}
