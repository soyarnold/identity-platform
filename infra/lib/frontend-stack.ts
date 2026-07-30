import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";

/**
 * Frontend scaffold — future home for:
 * - S3 buckets for apps/web (and optionally apps/demo) static builds
 * - CloudFront distributions (TLS, custom domains)
 * - Align FRONTEND_URL, CORS_ORIGINS, WEBAUTHN_ORIGINS, cookie domain
 *   with the CloudFront hostnames
 *
 * No AWS resources are created yet (phase 09 scaffold only).
 */
export class FrontendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // TODO(phase-later): s3.Bucket + cloudfront.Distribution for apps/web
    // TODO(phase-later): optional second distribution for apps/demo
    new cdk.CfnOutput(this, "FrontendStatus", {
      value: "scaffold-only",
      description:
        "Replace with CloudFront domain names when FrontendStack is implemented",
    });
  }
}
