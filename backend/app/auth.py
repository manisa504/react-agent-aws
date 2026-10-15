from fastapi import HTTPException, Request


def get_owner(request: Request) -> str:
    if request.app.state.demo:
        return "local-demo-user"
    # Only the API Gateway integration supplies this trusted scope, never HTTP headers.
    event = request.scope.get("aws.event", {})
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    owner = claims.get("sub")
    if not owner:
        raise HTTPException(status_code=401, detail="Sign in required")
    return owner
