import click

from jira_assistant_skills.utils import SKILLS_ROOT_DIR, run_skill_script_subprocess


@click.group()
def jsm():
    """Commands for Jira Service Management (service desks, requests, SLAs)."""
    pass


# Service Desk commands
@jsm.group(name="service-desk")
def service_desk():
    """Manage service desks."""
    pass


@service_desk.command(name="list")
@click.pass_context
def service_desk_list(ctx):
    """List all service desks."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "list_service_desks.py"
    run_skill_script_subprocess(script_path, [], ctx)


@service_desk.command(name="get")
@click.argument("service_desk_id", type=int)
@click.pass_context
def service_desk_get(ctx, service_desk_id: int):
    """Get service desk details."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_service_desk.py"
    run_skill_script_subprocess(script_path, [str(service_desk_id)], ctx)


@service_desk.command(name="create")
@click.argument("project_key")
@click.argument("name")
@click.option("--description", "-d", help="Service desk description")
@click.pass_context
def service_desk_create(ctx, project_key: str, name: str, description: str):
    """Create a new service desk."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "create_service_desk.py"

    script_args = [project_key, name]
    if description:
        script_args.extend(["--description", description])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Request Type commands
@jsm.group(name="request-type")
def request_type():
    """Manage request types."""
    pass


@request_type.command(name="list")
@click.argument("service_desk_id", type=int)
@click.pass_context
def request_type_list(ctx, service_desk_id: int):
    """List request types for a service desk."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "list_request_types.py"
    run_skill_script_subprocess(script_path, [str(service_desk_id)], ctx)


@request_type.command(name="get")
@click.argument("service_desk_id", type=int)
@click.argument("request_type_id", type=int)
@click.pass_context
def request_type_get(ctx, service_desk_id: int, request_type_id: int):
    """Get request type details."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_request_type.py"
    run_skill_script_subprocess(
        script_path, [str(service_desk_id), str(request_type_id)], ctx
    )


@request_type.command(name="fields")
@click.argument("service_desk_id", type=int)
@click.argument("request_type_id", type=int)
@click.pass_context
def request_type_fields(ctx, service_desk_id: int, request_type_id: int):
    """Get fields for a request type."""
    script_path = (
        SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_request_type_fields.py"
    )
    run_skill_script_subprocess(
        script_path, [str(service_desk_id), str(request_type_id)], ctx
    )


# Request commands
@jsm.group()
def request():
    """Manage service requests."""
    pass


@request.command(name="list")
@click.argument("service_desk_id", type=int)
@click.option("--status", "-s", help="Filter by status")
@click.option("--reporter", "-r", help="Filter by reporter")
@click.option("--max-results", "-m", type=int, default=50, help="Maximum results")
@click.pass_context
def request_list(
    ctx, service_desk_id: int, status: str, reporter: str, max_results: int
):
    """List requests for a service desk."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "list_requests.py"

    script_args = [str(service_desk_id)]
    if status:
        script_args.extend(["--status", status])
    if reporter:
        script_args.extend(["--reporter", reporter])
    if max_results:
        script_args.extend(["--max-results", str(max_results)])

    run_skill_script_subprocess(script_path, script_args, ctx)


@request.command(name="create")
@click.argument("service_desk_id", type=int)
@click.argument("request_type_id", type=int)
@click.option("--summary", "-s", required=True, help="Request summary")
@click.option("--description", "-d", help="Request description")
@click.option("--fields", "-f", help="Additional fields as JSON")
@click.option("--on-behalf-of", help="Create on behalf of customer")
@click.pass_context
def request_create(
    ctx,
    service_desk_id: int,
    request_type_id: int,
    summary: str,
    description: str,
    fields: str,
    on_behalf_of: str,
):
    """Create a new request."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "create_request.py"

    script_args = [str(service_desk_id), str(request_type_id), "--summary", summary]
    if description:
        script_args.extend(["--description", description])
    if fields:
        script_args.extend(["--fields", fields])
    if on_behalf_of:
        script_args.extend(["--on-behalf-of", on_behalf_of])

    run_skill_script_subprocess(script_path, script_args, ctx)


@request.command(name="get")
@click.argument("issue_key")
@click.pass_context
def request_get(ctx, issue_key: str):
    """Get request details."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_request.py"
    run_skill_script_subprocess(script_path, [issue_key], ctx)


@request.command(name="status")
@click.argument("issue_key")
@click.pass_context
def request_status(ctx, issue_key: str):
    """Get request status."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_request_status.py"
    run_skill_script_subprocess(script_path, [issue_key], ctx)


@request.command(name="transition")
@click.argument("issue_key")
@click.argument("status")
@click.option("--comment", "-c", help="Transition comment")
@click.pass_context
def request_transition(ctx, issue_key: str, status: str, comment: str):
    """Transition a request to a new status."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "transition_request.py"

    script_args = [issue_key, status]
    if comment:
        script_args.extend(["--comment", comment])

    run_skill_script_subprocess(script_path, script_args, ctx)


@request.command(name="comment")
@click.argument("issue_key")
@click.argument("body")
@click.option(
    "--internal",
    "-i",
    is_flag=True,
    help="Internal comment (agent-only, not visible to customers)",
)
@click.pass_context
def request_comment(ctx, issue_key: str, body: str, internal: bool):
    """Add a comment to a request."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "add_request_comment.py"

    script_args = [issue_key, "--body", body]
    if internal:
        script_args.append("--internal")

    run_skill_script_subprocess(script_path, script_args, ctx)


@request.command(name="comments")
@click.argument("issue_key")
@click.option("--public-only", "-p", is_flag=True, help="Show only public comments")
@click.option(
    "--internal-only", is_flag=True, help="Show only internal (agent-only) comments"
)
@click.option("--id", "comment_id", help="Get specific comment by ID")
@click.option("--all-pages", is_flag=True, help="Fetch all pages (default: first 100)")
@click.pass_context
def request_comments(
    ctx,
    issue_key: str,
    public_only: bool,
    internal_only: bool,
    comment_id: str,
    all_pages: bool,
):
    """Get comments for a request."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_request_comments.py"

    script_args = [issue_key]
    if public_only:
        script_args.append("--public-only")
    if internal_only:
        script_args.append("--internal-only")
    if comment_id:
        script_args.extend(["--id", comment_id])
    if all_pages:
        script_args.append("--all-pages")

    run_skill_script_subprocess(script_path, script_args, ctx)


# Participant commands
@request.command(name="participants")
@click.argument("issue_key")
@click.pass_context
def request_participants(ctx, issue_key: str):
    """Get participants for a request."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_participants.py"
    run_skill_script_subprocess(script_path, [issue_key], ctx)


@request.command(name="add-participant")
@click.argument("issue_key")
@click.argument("account_id")
@click.pass_context
def request_add_participant(ctx, issue_key: str, account_id: str):
    """Add a participant to a request."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "add_participant.py"
    run_skill_script_subprocess(script_path, [issue_key, account_id], ctx)


@request.command(name="remove-participant")
@click.argument("issue_key")
@click.argument("account_id")
@click.pass_context
def request_remove_participant(ctx, issue_key: str, account_id: str):
    """Remove a participant from a request."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "remove_participant.py"
    run_skill_script_subprocess(script_path, [issue_key, account_id], ctx)


# Customer commands
@jsm.group()
def customer():
    """Manage customers."""
    pass


@customer.command(name="list")
@click.argument("service_desk_id", type=int)
@click.option("--query", "-q", help="Search query")
@click.pass_context
def customer_list(ctx, service_desk_id: int, query: str):
    """List customers for a service desk."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "list_customers.py"

    script_args = [str(service_desk_id)]
    if query:
        script_args.extend(["--query", query])

    run_skill_script_subprocess(script_path, script_args, ctx)


@customer.command(name="create")
@click.argument("service_desk_id", type=int)
@click.argument("email")
@click.option("--display-name", "-n", help="Customer display name")
@click.pass_context
def customer_create(ctx, service_desk_id: int, email: str, display_name: str):
    """Create a new customer."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "create_customer.py"

    script_args = [str(service_desk_id), email]
    if display_name:
        script_args.extend(["--display-name", display_name])

    run_skill_script_subprocess(script_path, script_args, ctx)


@customer.command(name="add")
@click.argument("service_desk_id", type=int)
@click.argument("account_id")
@click.pass_context
def customer_add(ctx, service_desk_id: int, account_id: str):
    """Add an existing user as a customer."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "add_customer.py"
    run_skill_script_subprocess(script_path, [str(service_desk_id), account_id], ctx)


@customer.command(name="remove")
@click.argument("service_desk_id", type=int)
@click.argument("account_id")
@click.pass_context
def customer_remove(ctx, service_desk_id: int, account_id: str):
    """Remove a customer from a service desk."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "remove_customer.py"
    run_skill_script_subprocess(script_path, [str(service_desk_id), account_id], ctx)


# Organization commands
@jsm.group()
def organization():
    """Manage organizations."""
    pass


@organization.command(name="list")
@click.pass_context
def organization_list(ctx):
    """List all organizations."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "list_organizations.py"
    run_skill_script_subprocess(script_path, [], ctx)


@organization.command(name="get")
@click.argument("organization_id", type=int)
@click.pass_context
def organization_get(ctx, organization_id: int):
    """Get organization details."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_organization.py"
    run_skill_script_subprocess(script_path, [str(organization_id)], ctx)


@organization.command(name="create")
@click.argument("name")
@click.pass_context
def organization_create(ctx, name: str):
    """Create a new organization."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "create_organization.py"
    run_skill_script_subprocess(script_path, [name], ctx)


@organization.command(name="delete")
@click.argument("organization_id", type=int)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def organization_delete(ctx, organization_id: int, force: bool):
    """Delete an organization."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "delete_organization.py"

    script_args = [str(organization_id)]
    if force:
        script_args.append("--force")

    run_skill_script_subprocess(script_path, script_args, ctx)


@organization.command(name="add-customer")
@click.argument("organization_id", type=int)
@click.argument("account_id")
@click.pass_context
def organization_add_customer(ctx, organization_id: int, account_id: str):
    """Add a customer to an organization."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "add_to_organization.py"
    run_skill_script_subprocess(script_path, [str(organization_id), account_id], ctx)


@organization.command(name="remove-customer")
@click.argument("organization_id", type=int)
@click.argument("account_id")
@click.pass_context
def organization_remove_customer(ctx, organization_id: int, account_id: str):
    """Remove a customer from an organization."""
    script_path = (
        SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "remove_from_organization.py"
    )
    run_skill_script_subprocess(script_path, [str(organization_id), account_id], ctx)


# Queue commands
@jsm.group()
def queue():
    """Manage queues."""
    pass


@queue.command(name="list")
@click.argument("service_desk_id", type=int)
@click.option("--show-jql", is_flag=True, help="Show JQL queries for each queue")
@click.pass_context
def queue_list(ctx, service_desk_id: int, show_jql: bool):
    """List queues for a service desk."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "list_queues.py"
    script_args = ["--service-desk", str(service_desk_id)]
    if show_jql:
        script_args.append("--show-jql")
    run_skill_script_subprocess(script_path, script_args, ctx)


@queue.command(name="get")
@click.argument("service_desk_id", type=int)
@click.argument("queue_id", type=int)
@click.pass_context
def queue_get(ctx, service_desk_id: int, queue_id: int):
    """Get queue details."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_queue.py"
    run_skill_script_subprocess(
        script_path,
        ["--service-desk", str(service_desk_id), "--queue-id", str(queue_id)],
        ctx,
    )


@queue.command(name="issues")
@click.argument("service_desk_id", type=int)
@click.argument("queue_id", type=int)
@click.option("--max-results", "-m", type=int, default=50, help="Maximum results")
@click.pass_context
def queue_issues(ctx, service_desk_id: int, queue_id: int, max_results: int):
    """Get issues in a queue."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_queue_issues.py"
    run_skill_script_subprocess(
        script_path,
        [
            "--service-desk",
            str(service_desk_id),
            "--queue-id",
            str(queue_id),
            "--limit",
            str(max_results),
        ],
        ctx,
    )


# SLA commands
@jsm.group()
def sla():
    """Manage SLAs."""
    pass


@sla.command(name="get")
@click.argument("issue_key")
@click.pass_context
def sla_get(ctx, issue_key: str):
    """Get SLA information for an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_sla.py"
    run_skill_script_subprocess(script_path, [issue_key], ctx)


@sla.command(name="check-breach")
@click.argument("issue_key")
@click.pass_context
def sla_check_breach(ctx, issue_key: str):
    """Check if an issue is breaching SLA."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "check_sla_breach.py"
    run_skill_script_subprocess(script_path, [issue_key], ctx)


@sla.command(name="report")
@click.argument("service_desk_id", type=int)
@click.option("--since", "-s", help="Report start date")
@click.option("--until", help="Report end date")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "csv", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def sla_report(ctx, service_desk_id: int, since: str, until: str, output_format: str):
    """Generate SLA report."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "sla_report.py"

    script_args = [str(service_desk_id)]
    if since:
        script_args.extend(["--since", since])
    if until:
        script_args.extend(["--until", until])
    if output_format != "text":
        script_args.extend(["--format", output_format])

    run_skill_script_subprocess(script_path, script_args, ctx)


# Approval commands
@jsm.group()
def approval():
    """Manage approvals."""
    pass


@approval.command(name="list")
@click.argument("issue_key")
@click.pass_context
def approval_list(ctx, issue_key: str):
    """Get approvals for an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_approvals.py"
    run_skill_script_subprocess(script_path, [issue_key], ctx)


@approval.command(name="pending")
@click.option("--service-desk-id", "-s", type=int, help="Filter by service desk")
@click.pass_context
def approval_pending(ctx, service_desk_id: int):
    """List pending approvals."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "list_pending_approvals.py"

    script_args = []
    if service_desk_id:
        script_args.extend(["--service-desk-id", str(service_desk_id)])

    run_skill_script_subprocess(script_path, script_args, ctx)


@approval.command(name="approve")
@click.argument("issue_key")
@click.argument("approval_id", type=int)
@click.option("--comment", "-c", help="Approval comment")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be approved without making changes"
)
@click.pass_context
def approval_approve(
    ctx, issue_key: str, approval_id: int, comment: str, yes: bool, dry_run: bool
):
    """Approve a request."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "approve_request.py"

    script_args = [issue_key, "--approval-id", str(approval_id)]
    if comment:
        script_args.extend(["--comment", comment])
    if yes:
        script_args.append("--yes")
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)


@approval.command(name="decline")
@click.argument("issue_key")
@click.argument("approval_id", type=int)
@click.option("--comment", "-c", help="Decline comment")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be declined without making changes"
)
@click.pass_context
def approval_decline(
    ctx, issue_key: str, approval_id: int, comment: str, yes: bool, dry_run: bool
):
    """Decline a request."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "decline_request.py"

    script_args = [issue_key, "--approval-id", str(approval_id)]
    if comment:
        script_args.extend(["--comment", comment])
    if yes:
        script_args.append("--yes")
    if dry_run:
        script_args.append("--dry-run")

    run_skill_script_subprocess(script_path, script_args, ctx)


# Knowledge Base commands
@jsm.group()
def kb():
    """Manage Knowledge Base articles."""
    pass


@kb.command(name="search")
@click.argument("query")
@click.option("--service-desk-id", "-s", type=int, help="Limit to service desk")
@click.option("--max-results", "-m", type=int, default=10, help="Maximum results")
@click.pass_context
def kb_search(ctx, query: str, service_desk_id: int, max_results: int):
    """Search Knowledge Base articles."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "search_kb.py"

    script_args = [query]
    if service_desk_id:
        script_args.extend(["--service-desk-id", str(service_desk_id)])
    if max_results:
        script_args.extend(["--max-results", str(max_results)])

    run_skill_script_subprocess(script_path, script_args, ctx)


@kb.command(name="get")
@click.argument("article_id")
@click.pass_context
def kb_get(ctx, article_id: str):
    """Get a Knowledge Base article."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_kb_article.py"
    run_skill_script_subprocess(script_path, [article_id], ctx)


@kb.command(name="suggest")
@click.argument("issue_key")
@click.option("--max-results", "-m", type=int, default=5, help="Maximum suggestions")
@click.pass_context
def kb_suggest(ctx, issue_key: str, max_results: int):
    """Suggest KB articles for an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "suggest_kb.py"
    run_skill_script_subprocess(
        script_path, [issue_key, "--max-results", str(max_results)], ctx
    )


# Asset commands (JSM Premium)
@jsm.group()
def asset():
    """Manage Assets/CMDB (requires JSM Premium)."""
    pass


@asset.command(name="list")
@click.option("--schema", "-s", help="Object schema")
@click.option("--type", "-t", "object_type", help="Object type")
@click.option("--query", "-q", help="AQL query")
@click.option("--max-results", "-m", type=int, default=50, help="Maximum results")
@click.pass_context
def asset_list(ctx, schema: str, object_type: str, query: str, max_results: int):
    """List assets."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "list_assets.py"

    script_args = []
    if schema:
        script_args.extend(["--schema", schema])
    if object_type:
        script_args.extend(["--type", object_type])
    if query:
        script_args.extend(["--query", query])
    if max_results:
        script_args.extend(["--max-results", str(max_results)])

    run_skill_script_subprocess(script_path, script_args, ctx)


@asset.command(name="get")
@click.argument("object_id")
@click.pass_context
def asset_get(ctx, object_id: str):
    """Get asset details."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "get_asset.py"
    run_skill_script_subprocess(script_path, [object_id], ctx)


@asset.command(name="create")
@click.argument("object_type_id")
@click.option("--attributes", "-a", required=True, help="Attributes as JSON")
@click.pass_context
def asset_create(ctx, object_type_id: str, attributes: str):
    """Create a new asset."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "create_asset.py"
    run_skill_script_subprocess(
        script_path, [object_type_id, "--attributes", attributes], ctx
    )


@asset.command(name="update")
@click.argument("object_id")
@click.option("--attributes", "-a", required=True, help="Attributes to update as JSON")
@click.pass_context
def asset_update(ctx, object_id: str, attributes: str):
    """Update an asset."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "update_asset.py"
    run_skill_script_subprocess(
        script_path, [object_id, "--attributes", attributes], ctx
    )


@asset.command(name="link")
@click.argument("issue_key")
@click.argument("object_id")
@click.pass_context
def asset_link(ctx, issue_key: str, object_id: str):
    """Link an asset to an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "link_asset.py"
    run_skill_script_subprocess(script_path, [issue_key, object_id], ctx)


@asset.command(name="find-affected")
@click.argument("issue_key")
@click.pass_context
def asset_find_affected(ctx, issue_key: str):
    """Find assets affected by an issue."""
    script_path = SKILLS_ROOT_DIR / "jira-jsm" / "scripts" / "find_affected_assets.py"
    run_skill_script_subprocess(script_path, [issue_key], ctx)
