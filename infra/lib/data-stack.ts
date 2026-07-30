import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";

/**
 * Data plane scaffold — future home for:
 * - RDS PostgreSQL (private subnets, Secrets Manager credentials)
 * - ElastiCache Redis (sessions, WebAuthn challenges, OAuth auth codes)
 *
 * Maps to local Docker Compose services `postgres` + `redis`.
 * No AWS resources are created yet (phase 09 scaffold only).
 */
export class DataStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // TODO(phase-later): rds.DatabaseInstance or Aurora Serverless v2
    // TODO(phase-later): elasticache.CfnCacheCluster / ReplicationGroup
    new cdk.CfnOutput(this, "DataStatus", {
      value: "scaffold-only",
      description:
        "Replace with RDS endpoint + Redis primary endpoint when implemented",
    });
  }
}
