import { api } from "./client";
import type { AuthorizeParams } from "../oauth/params";

export type ConsentResponse = {
  redirect_to: string;
};

export function submitConsent(params: AuthorizeParams, approve: boolean) {
  return api<ConsentResponse>("/oauth/consent", {
    method: "POST",
    body: JSON.stringify({
      client_id: params.client_id,
      redirect_uri: params.redirect_uri,
      response_type: params.response_type,
      code_challenge: params.code_challenge,
      code_challenge_method: params.code_challenge_method,
      state: params.state,
      scope: params.scope,
      approve,
    }),
  });
}
