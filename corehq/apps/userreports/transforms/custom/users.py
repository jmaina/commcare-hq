from corehq.apps.users.util import cached_user_id_to_username, cached_owner_id_to_display

# these are just aliased here to make it clear what is supported
get_user_display = cached_user_id_to_username
get_owner_display = cached_owner_id_to_display
