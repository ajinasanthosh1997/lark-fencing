document.addEventListener('DOMContentLoaded', async () => {
  const API = '/api/v1';
  const CART_ID_KEY = 'larkCartId';
  const money = value => new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR' }).format(Number(value) || 0);
  const request = async (url, options = {}) => {
    const response = await fetch(url, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    });
    const data = response.status === 204 ? null : await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(Object.values(data || {}).flat().join(' ') || 'Request failed.');
    return data;
  };
  const productImage = product => product.gallery_images?.[0]?.image_url || '/static/assets/images/products/hd/solid-cottage.png';
  const syncCount = cart => document.querySelectorAll('[data-cart-count]').forEach(node => node.textContent = cart?.item_count || 0);

  async function getCart(create = true) {
    let id = localStorage.getItem(CART_ID_KEY);
    if (id) {
      try { const cart = await request(`${API}/carts/${id}/`); syncCount(cart); return cart; }
      catch { localStorage.removeItem(CART_ID_KEY); }
    }
    if (!create) return null;
    const cart = await request(`${API}/carts/`, { method: 'POST', body: '{}' });
    localStorage.setItem(CART_ID_KEY, cart.public_id);
    syncCount(cart);
    return cart;
  }

  async function findProduct(item) {
    const key = String(item.id || '').toLowerCase();
    if (key) {
      try { return await request(`${API}/products/${encodeURIComponent(key)}/`); }
      catch { /* Fall back to matching the paginated catalogue by name. */ }
    }
    const response = await request(`${API}/products/?search=${encodeURIComponent(item.name || item.id || '')}`);
    const products = Array.isArray(response) ? response : response.results || [];
    return products.find(product => product.slug === key)
      || products.find(product => product.name.toLowerCase() === String(item.name || '').toLowerCase())
      || products[0];
  }

  window.LarkCommerce = {
    async addProduct(item) {
      const product = await findProduct(item);
      if (!product) throw new Error('This product has not been added to the Django catalogue yet.');
      const cart = await getCart();
      return request(`${API}/carts/${cart.public_id}/items/`, {
        method: 'POST',
        body: JSON.stringify({ product_id: product.id, variant_id: item.variantId || null, quantity: Number(item.quantity) || 1, customization: item.customization || {} }),
      });
    },
  };

  document.querySelectorAll('[data-catalog-card]').forEach(card => {
    const variantSelect = card.querySelector('[data-card-variant]'), price = card.querySelector('[data-card-price]'), statusNode = card.querySelector('[data-card-status]');
    const syncPrice = () => { const selected = variantSelect?.selectedOptions[0]; if (selected && price) price.textContent = money(selected.dataset.price); };
    variantSelect?.addEventListener('change', syncPrice); syncPrice();
    const add = async redirect => {
      const buttons = card.querySelectorAll('[data-catalog-add],[data-catalog-buy]'); buttons.forEach(button => button.disabled = true);
      try {
        const cart = await window.LarkCommerce.addProduct({ id: card.dataset.productSlug, name: card.dataset.productName, quantity: 1, variantId: variantSelect?.value || null });
        syncCount(cart); statusNode.hidden = false; statusNode.textContent = 'Added to cart.';
        if (redirect) location.href = '/checkout/';
      } catch (error) { statusNode.hidden = false; statusNode.textContent = error.message; }
      finally { if (!redirect) buttons.forEach(button => button.disabled = false); }
    };
    card.querySelector('[data-catalog-add]')?.addEventListener('click', () => add(false));
    card.querySelector('[data-catalog-buy]')?.addEventListener('click', () => add(true));
  });

  const serverAddButton = document.querySelector('[data-server-add-cart]');
  const serverBuyButton = document.querySelector('[data-server-buy-now]');
  if (serverAddButton) {
    const variantSelect = document.querySelector('[data-product-variant]');
    const variantPicker = document.querySelector('[data-variant-picker]');
    const sizeButtons = [...document.querySelectorAll('[data-variant-size]')];
    const styleButtons = [...document.querySelectorAll('[data-variant-style]')];
    const setActive = (buttons, activeButton) => buttons.forEach(button => {
      const active = button === activeButton;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
    const selectMatchingVariant = () => {
      if (!variantSelect) return;
      const selectedSize = sizeButtons.find(button => button.classList.contains('active'))?.dataset.variantSize || '';
      const selectedStyle = styleButtons.find(button => button.classList.contains('active'))?.dataset.variantStyle || '';
      const option = [...variantSelect.options].find(item => item.dataset.size === selectedSize && (!selectedStyle || item.dataset.style === selectedStyle));
      if (!option) return;
      variantSelect.value = option.value;
      variantSelect.dispatchEvent(new Event('change', { bubbles: true }));
    };
    const syncVariant = () => {
      const option = variantSelect?.selectedOptions[0];
      if (!option) return;
      document.querySelector('.detail-price strong').textContent = money(option.dataset.price);
      document.querySelector('.detail-points li:nth-child(2)').textContent = `Selected option price: ${money(option.dataset.price)}`;
      document.querySelector('.detail-points li:nth-child(3)').textContent = Number(option.dataset.stock) ? `${option.dataset.stock} currently available` : 'Contact us for availability';
      const sku = document.querySelector('.detail-copy > .eyebrow');
      if (sku && option.dataset.sku) sku.textContent = option.dataset.sku;
    };
    variantSelect?.addEventListener('change', syncVariant); syncVariant();
    sizeButtons.forEach(button => button.addEventListener('click', () => { setActive(sizeButtons, button); selectMatchingVariant(); }));
    styleButtons.forEach(button => button.addEventListener('click', () => { setActive(styleButtons, button); selectMatchingVariant(); }));
    variantPicker?.classList.add('is-ready');
    selectMatchingVariant();
    const addCurrentProduct = async () => {
      const quantity = Number(document.querySelector('#order-quantity')?.value) || 1;
      const variantId = document.querySelector('[data-product-variant]')?.value || null;
      const cart = await window.LarkCommerce.addProduct({
        id: serverAddButton.dataset.productSlug,
        name: serverAddButton.dataset.productName,
        quantity, variantId,
      });
      syncCount(cart);
      return cart;
    };
    serverAddButton.addEventListener('click', async () => {
      serverAddButton.disabled = true;
      try {
        await addCurrentProduct();
        serverAddButton.innerHTML = 'Added to cart <span>✓</span>';
      } catch (error) {
        serverAddButton.textContent = error.message;
      } finally {
        setTimeout(() => { serverAddButton.disabled = false; serverAddButton.innerHTML = 'Add to cart <span>→</span>'; }, 1600);
      }
    });
    serverBuyButton?.addEventListener('click', async () => {
      serverBuyButton.disabled = true;
      try { await addCurrentProduct(); location.href = '/checkout/'; }
      catch (error) { serverBuyButton.disabled = false; serverBuyButton.textContent = error.message; }
    });
  }

  getCart(false).catch(() => {});

  const empty = document.querySelector('[data-cart-empty]');
  const content = document.querySelector('[data-cart-content]');
  const list = document.querySelector('[data-cart-list]');
  const drawCart = async () => {
    if (!list) return;
    const cart = await getCart(false);
    const items = cart?.items || [];
    syncCount(cart);
    empty.hidden = items.length > 0;
    content.hidden = items.length === 0;
    list.replaceChildren();
    items.forEach(item => {
      const article = document.createElement('article'); article.className = 'cart-item';
      article.innerHTML = `<img src="${productImage(item.product)}" alt=""><div><small>${item.product.category?.name || 'Fencing'}</small><h2>${item.product.name}</h2><p>${item.variant ? `Size: ${item.variant.name}` : (item.product.description || '')}</p><strong class="cart-item-price">${money(item.variant?.price || item.product.price)} each</strong><label>Quantity <input type="number" min="1" max="${item.variant?.stock_quantity || item.product.stock_quantity || 99}" value="${item.quantity}"></label></div><button type="button">Remove</button>`;
      article.querySelector('input').addEventListener('change', async event => {
        await request(`${API}/carts/${cart.public_id}/items/${item.id}/`, { method: 'PATCH', body: JSON.stringify({ quantity: Number(event.target.value) || 1 }) });
        drawCart();
      });
      article.querySelector('button').addEventListener('click', async () => {
        await request(`${API}/carts/${cart.public_id}/items/${item.id}/`, { method: 'DELETE' });
        drawCart();
      });
      list.append(article);
    });
    document.querySelectorAll('[data-cart-subtotal],[data-cart-total]').forEach(node => node.textContent = money(cart?.subtotal));
  };
  drawCart().catch(console.error);

  const checkoutForm = document.querySelector('[data-checkout-form]');
  if (checkoutForm) {
    const cart = await getCart(false);
    const items = cart?.items || [];
    document.querySelector('[data-checkout-empty]').hidden = items.length > 0;
    document.querySelector('[data-checkout-content]').hidden = items.length === 0;
    const rows = document.querySelector('[data-checkout-items]');
    items.forEach(item => rows.insertAdjacentHTML('beforeend', `<article class="checkout-item"><img src="${productImage(item.product)}" alt=""><div><strong>${item.product.name}</strong><small>${item.variant ? `${item.variant.name} · ` : ''}Qty ${item.quantity}</small></div><b>${money(item.line_total)}</b></article>`));
    document.querySelector('[data-checkout-subtotal]').textContent = money(cart?.subtotal);
    document.querySelector('[data-checkout-total]').textContent = money(cart?.subtotal);
    checkoutForm.addEventListener('submit', async event => {
      event.preventDefault();
      const message = document.querySelector('[data-checkout-message]');
      let valid = true;
      checkoutForm.querySelectorAll('[required]').forEach(field => {
        const ok = field.type === 'checkbox' ? field.checked : field.checkValidity() && String(field.value).trim();
        field.closest('label')?.classList.toggle('invalid', !ok); valid = valid && Boolean(ok);
      });
      if (!valid) { message.hidden = false; message.className = 'checkout-message error'; message.textContent = 'Please complete all required fields.'; return; }
      const form = new FormData(checkoutForm);
      const payload = {
        payment_method: 'cash_on_delivery', fulfilment_method: 'delivery',
        first_name: form.get('firstName'), last_name: form.get('lastName'), email: form.get('email'), phone: form.get('phone'),
        address_line_1: form.get('address'), address_line_2: form.get('address2') || '', city: form.get('city'), county: form.get('county'),
        postal_code: form.get('eircode'), country_code: 'IE', customer_notes: form.get('notes') || '',
        items: items.map(item => ({ product_id: item.product.id, variant_id: item.variant?.id || null, quantity: item.quantity, customization: item.customization || {} })),
      };
      const button = document.querySelector('[data-pay-button]'); button.disabled = true; button.textContent = 'Creating order…';
      try {
        const order = await request(`${API}/orders/`, { method: 'POST', body: JSON.stringify(payload) });
        await request(`${API}/carts/${cart.public_id}/`, { method: 'DELETE' }); localStorage.removeItem(CART_ID_KEY);
        message.hidden = false; message.className = 'checkout-message success'; message.innerHTML = `<strong>Order ${order.order_number} created.</strong><p>We sent the order details to ${order.email}.</p>`;
        button.textContent = 'Order confirmed'; syncCount(null);
      } catch (error) { button.disabled = false; button.innerHTML = 'Place cash-on-delivery order <span>→</span>'; message.hidden = false; message.className = 'checkout-message error'; message.textContent = error.message; }
    });
  }
});
