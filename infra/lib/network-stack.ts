import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";

/**
 * Network scaffold — future home for:
 * - VPC (public + private subnets across 2+ AZs)
 * - NAT (or VPC endpoints) for private Fargate tasks
 * - Security groups: ALB → API, API → RDS, API → Redis
 *
 * No AWS resources are created yet (phase 09 scaffold only).
 */
export class NetworkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // TODO(phase-later): ec2.Vpc with maxAzs: 2, natGateways: 1 (or 0 + endpoints)
    new cdk.CfnOutput(this, "NetworkStatus", {
      value: "scaffold-only",
      description: "Replace with VPC id when NetworkStack is implemented",
    });
  }
}
