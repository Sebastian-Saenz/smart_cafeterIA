function oauthSignIn() {
    const params = {
      client_id: '401510539727-kmju5p4gsbitskfkvu6q4cmr2a0ht3ng.apps.googleusercontent.com',
      redirect_uri: 'https://8080-cs-6d82139e-bba8-403a-8cef-00afd4e3f4ac.cs-us-east1-pkhd.cloudshell.dev/auth/callback',
      response_type: 'code',
      scope: 'openid email profile',
      include_granted_scopes: 'true',
      state: 'random_' + Math.random().toString(36).substr(2)
    };
    // Guarda el state para verificar luego
    localStorage.setItem('oauth_state', params.state);
    const url = 'https://accounts.google.com/o/oauth2/v2/auth?' + new URLSearchParams(params);
    window.location = url;
  }