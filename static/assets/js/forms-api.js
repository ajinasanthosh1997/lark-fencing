document.addEventListener('DOMContentLoaded', () => {
  const API = '/api/v1';
  const TOKEN_KEY = 'larkAuthToken';
  const USER_KEY = 'larkAuthUser';

  const api = async (path, options = {}) => {
    const token = localStorage.getItem(TOKEN_KEY);
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Token ${token}` } : {}),
        ...(options.headers || {}),
      },
    });
    const data = response.status === 204 ? null : await response.json().catch(() => ({}));
    if (!response.ok) {
      const messages = Object.entries(data || {}).flatMap(([field, value]) =>
        (Array.isArray(value) ? value : [value]).map(message => `${field === 'non_field_errors' ? '' : `${field}: `}${message}`)
      );
      throw new Error(messages.join(' ') || 'Please try again.');
    }
    return data;
  };

  const saveAuth = data => {
    localStorage.setItem(TOKEN_KEY, data.token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    localStorage.setItem('larkSession', 'active');
  };

  document.querySelectorAll('[data-register-form]').forEach(form => form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.checkValidity()) return form.reportValidity();
    const fields = new FormData(form);
    const message = form.querySelector('.account-message');
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      const data = await api('/auth/signup/', { method: 'POST', body: JSON.stringify({
        first_name: fields.get('firstName'), last_name: fields.get('lastName'), email: fields.get('email'), password: fields.get('password'),
      }) });
      saveAuth(data);
      location.href = '/account/';
    } catch (error) {
      message.hidden = false; message.textContent = error.message; button.disabled = false;
    }
  }));

  document.querySelector('[data-login-form]')?.addEventListener('submit', async event => {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.checkValidity()) return form.reportValidity();
    const fields = new FormData(form), message = form.querySelector('.account-message'), button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      saveAuth(await api('/auth/login/', { method: 'POST', body: JSON.stringify({ email: fields.get('email'), password: fields.get('password') }) }));
      location.href = '/account/';
    } catch (error) { message.hidden = false; message.textContent = error.message; button.disabled = false; }
  });

  const resetLink = document.querySelector('.form-inline a[href^="mailto:"]');
  resetLink?.addEventListener('click', async event => {
    event.preventDefault();
    const email = document.querySelector('[data-login-form] [name="email"]')?.value.trim() || prompt('Enter your account email address:');
    if (!email) return;
    const result = await api('/auth/password/reset/', { method: 'POST', body: JSON.stringify({ email }) });
    const message = document.querySelector('[data-login-form] .account-message'); message.hidden = false; message.textContent = result.detail;
  });
  const resetParams = new URLSearchParams(location.search);
  if (resetParams.get('reset_uid') && resetParams.get('reset_token')) {
    const loginForm = document.querySelector('[data-login-form]');
    if (loginForm) {
      loginForm.innerHTML = `<label><span>New password</span><input type="password" name="new_password" minlength="8" required></label><button class="button" type="submit">Reset password <span>→</span></button><p class="account-message" role="status" hidden></p>`;
      loginForm.addEventListener('submit', async event => { event.preventDefault(); event.stopImmediatePropagation(); const message=loginForm.querySelector('.account-message'); try { const result=await api('/auth/password/reset/confirm/', {method:'POST',body:JSON.stringify({uid:resetParams.get('reset_uid'),token:resetParams.get('reset_token'),new_password:loginForm.elements.new_password.value})}); message.hidden=false;message.textContent=result.detail;setTimeout(()=>location.href='/login/',1200); } catch(error){message.hidden=false;message.textContent=error.message;} }, true);
    }
  }

  const user = (() => { try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; } })();
  if (user) {
    document.querySelector('[data-guest-panel]')?.setAttribute('hidden', '');
    document.querySelector('[data-member-panel]')?.removeAttribute('hidden');
    document.querySelector('[data-sign-out]')?.removeAttribute('hidden');
    document.querySelectorAll('[data-account-name],[data-detail-name]').forEach(node => node.textContent = `${user.first_name} ${user.last_name}`.trim() || user.email);
    document.querySelectorAll('[data-account-email],[data-detail-email]').forEach(node => node.textContent = user.email);
    document.querySelectorAll('[data-account-first-name]').forEach(node => node.textContent = user.first_name || 'there');
    document.querySelectorAll('[data-account-initial]').forEach(node => node.textContent = (user.first_name || user.email || 'L')[0].toUpperCase());
    const memberPanel = document.querySelector('[data-member-panel]');
    if (memberPanel) {
      const accountNav = document.querySelector('.account-menu nav');
      if (accountNav && !accountNav.querySelector('[href="#orders"]')) {
        accountNav.insertAdjacentHTML('beforeend', '<a href="#orders">Orders</a><a href="#addresses">Saved addresses</a><a href="#security">Security</a>');
      }
      memberPanel.insertAdjacentHTML('beforeend', `<section class="account-card" id="orders"><p class="eyebrow">Order history</p><h2>Your orders.</h2><div data-account-orders><p>Loading orders…</p></div></section><section class="account-card" id="addresses"><p class="eyebrow">Delivery details</p><h2>Saved addresses.</h2><div data-account-addresses></div><form class="account-form" data-address-form><div class="form-pair"><label><span>Label</span><input name="label" value="Home" required></label><label><span>Full name</span><input name="full_name" required></label></div><label><span>Phone</span><input name="phone"></label><label><span>Address</span><input name="address_line_1" required></label><label><span>Address line 2</span><input name="address_line_2"></label><div class="form-pair"><label><span>City</span><input name="city" required></label><label><span>County</span><input name="county" required></label></div><label><span>Eircode</span><input name="postal_code"></label><label class="check-label"><input type="checkbox" name="is_default"><span>Use as default address</span></label><button class="button" type="submit">Save address</button><p class="account-message" role="status" hidden></p></form></section><section class="account-card" id="security"><p class="eyebrow">Security</p><h2>Change password.</h2><form class="account-form" data-password-form><label><span>Current password</span><input type="password" name="current_password" required></label><label><span>New password</span><input type="password" name="new_password" required minlength="8"></label><button class="button" type="submit">Change password</button><p class="account-message" role="status" hidden></p></form></section>`);
      accountNav?.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', () => {
        accountNav.querySelectorAll('a').forEach(item => item.classList.toggle('active', item === link));
      }));
      const listData = data => Array.isArray(data) ? data : (data?.results || []);
      api('/auth/orders/').then(data => {
        const orders = listData(data), wrap = document.querySelector('[data-account-orders]');
        wrap.innerHTML = orders.length ? orders.map(order => `<article class="account-order"><div><strong>${order.order_number}</strong><small>${new Date(order.created_at).toLocaleDateString('en-IE')} · ${order.status.replaceAll('_', ' ')}</small></div><b>€${order.total}</b><details><summary>View order details</summary><p>${order.first_name} ${order.last_name}<br>${order.address_line_1}${order.address_line_2 ? `<br>${order.address_line_2}` : ''}<br>${order.city}, ${order.county} ${order.postal_code || ''}</p>${(order.order_items || []).map(item => `<p><strong>${item.product_name}${item.variant_name ? ` — ${item.variant_name}` : ''}</strong><br>${item.quantity} × €${item.unit_price} = €${item.line_total}</p>`).join('')}</details></article>`).join('') : '<p>No orders are associated with this email address yet.</p>';
      }).catch(error => document.querySelector('[data-account-orders]').textContent = error.message);
      const loadAddresses = () => api('/auth/addresses/').then(data => { const addresses = listData(data), wrap = document.querySelector('[data-account-addresses]'); wrap.innerHTML = addresses.length ? addresses.map(address => `<article class="account-address"><strong>${address.label}${address.is_default ? ' · Default' : ''}</strong><p>${address.full_name}<br>${address.address_line_1}${address.address_line_2 ? `<br>${address.address_line_2}` : ''}<br>${address.city}, ${address.county} ${address.postal_code || ''}</p><button type="button" data-delete-address="${address.id}">Remove</button></article>`).join('') : '<p>No saved addresses.</p>'; wrap.querySelectorAll('[data-delete-address]').forEach(button => button.addEventListener('click', async () => { await api(`/auth/addresses/${button.dataset.deleteAddress}/`, { method: 'DELETE' }); loadAddresses(); })); });
      loadAddresses();
      document.querySelector('[data-address-form]').addEventListener('submit', async event => { event.preventDefault(); const form = event.currentTarget, data = Object.fromEntries(new FormData(form)); data.country_code = 'IE'; data.is_default = form.elements.is_default.checked; try { await api('/auth/addresses/', { method: 'POST', body: JSON.stringify(data) }); form.reset(); loadAddresses(); } catch (error) { const message=form.querySelector('.account-message'); message.hidden=false; message.textContent=error.message; } });
      document.querySelector('[data-password-form]').addEventListener('submit', async event => { event.preventDefault(); const form=event.currentTarget, data=Object.fromEntries(new FormData(form)), message=form.querySelector('.account-message'); try { const result=await api('/auth/password/change/', {method:'POST',body:JSON.stringify(data)}); message.hidden=false; message.textContent=result.detail; [TOKEN_KEY,USER_KEY,'larkSession'].forEach(key=>localStorage.removeItem(key)); setTimeout(()=>location.href='/login/',1200); } catch(error){message.hidden=false;message.textContent=error.message;} });
    }
  }

  document.querySelector('[data-sign-out]')?.addEventListener('click', async () => {
    try { await api('/auth/logout/', { method: 'POST', body: '{}' }); } catch (_) { /* Clear an expired local session too. */ }
    [TOKEN_KEY, USER_KEY, 'larkSession'].forEach(key => localStorage.removeItem(key));
    location.href = '/login/';
  });

  const bindSubmission = (selector, path, payload) => {
    const form = document.querySelector(selector);
    if (!form) return;
    form.addEventListener('submit', async event => {
      event.preventDefault(); event.stopImmediatePropagation();
      if (!form.checkValidity()) return form.reportValidity();
      const button = form.querySelector('button[type="submit"]'), success = form.querySelector('.success-message');
      button.disabled = true;
      try {
        await api(path, { method: 'POST', body: JSON.stringify(payload(new FormData(form))) });
        if (success) success.hidden = false;
        button.textContent = 'Submitted';
      } catch (error) { button.disabled = false; button.textContent = error.message; }
    }, true);
  };

  bindSubmission('#quote-form', '/core/quote-requests/', data => ({
    first_name: data.get('firstName'), last_name: data.get('lastName'), email: data.get('email'), phone: data.get('phone') || '',
    address: data.get('address'), design: data.get('design') || '', approximate_length: data.get('length') || '', message: data.get('message') || '', consent: data.get('consent') === 'on',
  }));
  bindSubmission('#contact-form', '/core/contact-enquiries/', data => ({
    name: data.get('name'), email: data.get('email'), phone: data.get('phone') || '', subject: data.get('subject') || '', message: data.get('message'), consent: data.get('consent') === 'on',
  }));

  document.addEventListener('submit', async event => {
    const form = event.target.closest('[data-review-form]');
    if (!form) return;
    event.preventDefault(); event.stopImmediatePropagation();
    if (!form.checkValidity()) return form.reportValidity();
    const data = new FormData(form), button = form.querySelector('button[type="submit"]'), status = form.querySelector('[data-review-status]');
    button.disabled = true;
    try {
      await api('/core/customer-reviews/', { method: 'POST', body: JSON.stringify({ reviewer: data.get('reviewer'), project: data.get('project'), rating: Number(data.get('rating')), review: data.get('review'), permission: data.get('permission') === 'on' }) });
      status.hidden = false; status.textContent = 'Thank you. Your review was submitted for approval.'; button.textContent = 'Review submitted';
    } catch (error) { status.hidden = false; status.textContent = error.message; button.disabled = false; }
  }, true);
});
