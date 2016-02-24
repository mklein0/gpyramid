<!DOCTYPE html>
<html>
<head>
<title>List of Oauth2 Clients</title>
<style type="text/css">
	td, th { padding: 0.25em 1em }
</style>
</head>
<body>
<p>
    <a href="..">Back to index</a>
</p>
<h1>List of OAuth2 Clients</h1>

% if paginator.items:
${paginator.pager() | n}
<p>
<table border="1">
	<tr>
		<th></th>
		<th>Client ID</th>
		<th>Client Secret</th>
		<th>Email</th>
		<th>Redirect URI</th>
	</tr>
% for pos, client in enumerate(paginator.items, (items_per_page * (page_num - 1) + 1)):
	<tr>
		<td>${pos}.</td>
		<td><a href="${request.route_path('data.client.view_or_edit', client_id=client.client_id)}">${client.client_id}</a></td>
		<td>${client.client_secret}</td>
		<td>${client.email}</td>
		<td>${client.redirect_uri}</td>
	</tr>

% endfor
</table>
</p>
${paginator.pager() | n}
%else:
<ul>
	<li><strong>No Clients Found.</strong></li>
</ul>
%endif

<h1>Add Client</h1>
<p/>
<form method="POST" ><table>
% for field in (form.name, form.client_type, form.email, form.redirect_uri, form.home_page, form.client_id, form.client_secret,):
	<tr><th>${ field.label }</th><td>${ field() }<td></tr>
	% if field.errors:
	<tr><th></th><td>
		<ul>
		% for error in field.errors:
			<li>${ error }</li>
		% endfor
		</ul>
	</td></tr>
	% endif
% endfor
	<tr><th></th><td><input type="submit" value="Add New Client" /></td></tr>
</table></form>
</body>
</html>
<!--
# vim: set syntax=mako ts=2 sts=2 ai
-->
