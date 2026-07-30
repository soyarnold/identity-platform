#!/usr/bin/env node
/**
 * Identity Platform — CDK app entrypoint (scaffold only).
 *
 * Stacks below are placeholders. Do not `cdk deploy` until each stack is
 * implemented and reviewed. Local development continues to use Docker Compose.
 */
import * as cdk from "aws-cdk-lib";
import { ApiStack } from "../lib/api-stack";
import { DataStack } from "../lib/data-stack";
import { FrontendStack } from "../lib/frontend-stack";
import { NetworkStack } from "../lib/network-stack";

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION ?? "us-west-2",
};

// Order sketches dependencies: network → data/api → frontend.
// Real stack props (vpc, SG ids) will be wired when constructs exist.
new NetworkStack(app, "IdentityNetwork", {
  env,
  description: "VPC + subnets + security-group stubs (scaffold)",
});

new DataStack(app, "IdentityData", {
  env,
  description: "RDS Postgres + ElastiCache Redis stubs (scaffold)",
});

new ApiStack(app, "IdentityApi", {
  env,
  description: "ECS/Fargate API service stubs (scaffold)",
});

new FrontendStack(app, "IdentityFrontend", {
  env,
  description: "S3 + CloudFront static hosting stubs (scaffold)",
});

app.synth();
