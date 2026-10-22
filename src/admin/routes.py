from flask import (Blueprint, Response, abort, flash, redirect,
                   render_template, request, url_for)

from src.admin import (auth, backups, db_stats, sql_console, staged_changes,
                       user_stats)

bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")


@bp.before_request
def guard():
    if not auth.is_enabled():
        abort(404)
    if request.method == "POST" and not auth.csrf_valid(request.form.get("csrf_token")):
        abort(400)
    if request.endpoint != "admin.login" and not auth.is_logged_in():
        return redirect(url_for("admin.login"))


@bp.context_processor
def template_helpers():
    return {
        "csrf_token": auth.csrf_token,
        "human_bytes": db_stats.human_bytes,
        "pending": staged_changes.current(),
    }


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if auth.password_matches(request.form.get("password", "")):
            auth.log_in()
            return redirect(url_for("admin.dashboard"))
        return render_template("admin/login.html", error="Wrong password."), 401
    return render_template("admin/login.html", error=None)


@bp.route("/logout", methods=["POST"])
def logout():
    auth.log_out()
    return redirect(url_for("admin.login"))


@bp.route("/")
def dashboard():
    days = db_stats.readings_per_day()
    return render_template(
        "admin/dashboard.html",
        overview=db_stats.overview(),
        users=user_stats.all_users(),
        days=days,
        busiest_day=max((count for _, count in days), default=0),
        backups=backups.list_backups(),
    )


@bp.route("/sql", methods=["GET", "POST"])
def sql():
    if request.method == "GET":
        return render_template("admin/sql.html", examples=sql_console.EXAMPLES,
                               sql=request.args.get("sql", ""), allow_write=False,
                               result=None, error=None)
    query = request.form.get("sql", "")
    allow_write = request.form.get("allow_write") == "on"
    result, error = None, None
    try:
        result = staged_changes.submit(query, allow_write)
    except (sql_console.QueryRejected, sql_console.QueryFailed) as problem:
        error = str(problem)
    if result and request.form.get("action") == "csv":
        return Response(
            sql_console.to_csv(result),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=query.csv"},
        )
    return render_template("admin/sql.html", examples=sql_console.EXAMPLES, sql=query,
                           allow_write=allow_write, result=result, error=error)


@bp.route("/users/<username>")
def user(username):
    return render_template(
        "admin/user.html",
        username=username,
        stats=next((u for u in user_stats.all_users() if u.username == username), None),
        devices=user_stats.devices_for(username),
        recent=user_stats.recent_readings(username),
        deleted=request.args.get("deleted"),
    )


@bp.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    try:
        staged_changes.stage(
            "DELETE FROM data WHERE username = %s", (username,),
            label=f"DELETE all readings posted as {username!r}",
        )
    except sql_console.QueryFailed as problem:
        flash(str(problem))
        return redirect(url_for("admin.user", username=username))
    return redirect(url_for("admin.sql"))


@bp.route("/pending/commit", methods=["POST"])
def commit_pending():
    return _finish_pending(staged_changes.commit, "Committed {} statement(s).")


@bp.route("/pending/rollback", methods=["POST"])
def rollback_pending():
    return _finish_pending(staged_changes.rollback, "Rolled back {} statement(s). Nothing was changed.")


def _finish_pending(finish, message):
    try:
        flash(message.format(len(finish())))
    except staged_changes.NothingPending:
        flash("There were no pending changes (they may have timed out and been rolled back).")
    return redirect(url_for("admin.dashboard"))


@bp.route("/backups", methods=["POST"])
def back_up_now():
    flash(f"Backed up to schema {backups.create()}.")
    return redirect(url_for("admin.dashboard"))
