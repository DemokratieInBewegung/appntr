var Application = {
    loadMarktplatzInfo: function (username) {
        username = username.replace('@', '');
        fetch("https://marktplatz.bewegung.jetzt/u/" + username + ".json?stats=true").then(
            response => {
                if (response.status) {
                    response.json().then(data => {
                        if (typeof data.user != "undefined") {

                            data.user.avatar_template = data.user.avatar_template.replace('{size}', '80');
                            data.user.created_at = Application.formatDate(data.user.created_at);
                            data.user.last_posted_at = Application.formatDate(data.user.last_posted_at);
                            data.user.last_seen_at = Application.formatDate(data.user.last_seen_at);

                            var tmpl = $('#tmpl_marktplatz_info').text();
                            $('.card-block-user').append(ejs.render(tmpl, data));
                        }
                    })
                }
            }
        )
    },
    formatDate: function (dateStr) {
        var date = new Date(dateStr);
        return date.toLocaleDateString('de') + ' ' + date.toLocaleTimeString('de');
    }
};