document.addEventListener('DOMContentLoaded', () => {
    // Ensure Geoapify library is loaded
    if (!window.Geoapify) {
        console.error('Geoapify library not loaded.');
        return;
    }

    // Find all inputs with id starting with "stop-input"
    const stopInputs = document.querySelectorAll('input[id^="stop-input"]');
    if (stopInputs.length === 0) {
        console.warn('No inputs found with id starting with "stop-input".');
    }

    stopInputs.forEach((stopInput) => {
        const stopPlaceIdInput = stopInput.parentElement.querySelector('input[id$="place-id"]');
        if (!stopPlaceIdInput) {
            console.warn('No stop-place-id input found for stop-input:', stopInput);
        }

        const autocomplete = new Geoapify.GeocoderAutocomplete(
            stopInput,
            {
                apiKey: GEOAPIFY_API_KEY,
                type: 'address',
                countryCodes: ['us'],
                debounceDelay: 300,
                placeholder: stopInput.getAttribute('placeholder') || 'Enter stop location',
                lang: 'en'
            }
        );

        autocomplete.on('select', (location) => {
            if (location) {
                stopInput.value = location.properties.formatted || '';
                if (stopPlaceIdInput) {
                    stopPlaceIdInput.value = location.properties.place_id || '';
                }
            }
        });

        autocomplete.on('clear', () => {
            stopInput.value = '';
            if (stopPlaceIdInput) {
                stopPlaceIdInput.value = '';
            }
        });
    });

    // Search Functionality
    const searchInput = document.getElementById('ride-search');
    const searchButton = document.getElementById('ride-search-btn');
    const noResults = document.getElementById('no-results');
    const sharedRidesContainer = document.getElementById('shared-rides');
    const bookedRidesContainer = document.getElementById('booked-rides');
    const rideTemplates = document.getElementById('ride-card-templates');
    const bookingTemplates = document.getElementById('booking-card-templates');

    // Reusable search function
    const performSearch = () => {
        const query = searchInput.value.trim().toLowerCase();
        let hasResults = false;
        console.log('Performing search with query:', query);

        // Clear containers
        if (sharedRidesContainer) sharedRidesContainer.innerHTML = '';
        if (bookedRidesContainer) bookedRidesContainer.innerHTML = '';

        // Filter shared rides
        if (rideTemplates && sharedRidesContainer) {
            const sharedRideCards = rideTemplates.querySelectorAll('.ride-card');
            sharedRideCards.forEach(card => {
                const name = card.dataset.name || '';
                const destination = card.dataset.destination || '';
                if (query && (name.includes(query) || destination.includes(query))) {
                    const clone = card.cloneNode(true);
                    sharedRidesContainer.appendChild(clone);
                    hasResults = true;
                }
            });
        }

        // Filter booked rides
        if (bookingTemplates && bookedRidesContainer) {
            const bookedRideCards = bookingTemplates.querySelectorAll('.ride-card');
            bookedRideCards.forEach(card => {
                const vehicleModel = card.dataset.vehicleModel || '';
                const destination = card.dataset.destination || '';
                if (query && (vehicleModel.includes(query) || destination.includes(query))) {
                    const clone = card.cloneNode(true);
                    bookedRidesContainer.appendChild(clone);
                    hasResults = true;
                }
            });
        }

        // Show no-results message if needed
        if (noResults) {
            noResults.classList.toggle('d-none', hasResults || !query);
        }
    };

    if (searchInput) {
        // Real-time search on input
        searchInput.addEventListener('input', performSearch);
    }

    if (searchButton) {
        // Search on button click
        searchButton.addEventListener('click', () => {
            console.log('Search button clicked');
            performSearch();
        });
    }

    // Sort Functionality
    const sortSelect = document.getElementById('ride-sort');
    if (sortSelect) {
        sortSelect.addEventListener('change', () => {
            const [sortBy, order] = sortSelect.value.split('-');
            const sortCards = (container) => {
                if (!container) return;
                const cards = Array.from(container.querySelectorAll('.ride-card'));
                cards.sort((a, b) => {
                    let aValue = a.dataset[sortBy];
                    let bValue = b.dataset[sortBy];
                    if (sortBy === 'time') {
                        aValue = new Date(aValue).getTime();
                        bValue = new Date(bValue).getTime();
                        return order === 'asc' ? aValue - bValue : bValue - aValue;
                    } else if (sortBy === 'people') {
                        aValue = parseInt(aValue, 10);
                        bValue = parseInt(bValue, 10);
                        return order === 'asc' ? aValue - bValue : bValue - aValue;
                    } else {
                        return order === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(bValue);
                    }
                });
                container.innerHTML = '';
                cards.forEach(card => container.appendChild(card));
            };
            sortCards(sharedRidesContainer);
            sortCards(bookedRidesContainer);
        });
    }

    // SocketIO Chat
    const socket = io();

    socket.on('connect', () => {
        console.log('SocketIO connected:', socket.id);
    });

    socket.on('connect_error', (error) => {
        console.error('SocketIO connection error:', error);
        alert('Failed to connect to chat server. Please refresh the page.');
    });

    // Debug join/leave
    socket.on('message', (data) => {
        console.log('Received SocketIO message:', data);
        if (data.msg) {
            // System message (e.g., join/leave)
            const [type, id] = data.room.split('-');
            const chatDiv = document.getElementById(`chat-messages-${type}-${id}`);
            if (chatDiv) {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'mb-2 text-muted';
                messageDiv.textContent = data.msg;
                chatDiv.appendChild(messageDiv);
                chatDiv.scrollTop = chatDiv.scrollHeight;
                console.log('Appended system message:', data.msg);
            } else {
                console.warn('Chat div not found for room:', data.room);
            }
        } else {
            // User message
            const { user, content, timestamp, room } = data;
            const [type, id] = room.split('-');
            const chatDiv = document.getElementById(`chat-messages-${type}-${id}`);
            if (chatDiv) {
                const currentUser = chatDiv.parentElement.querySelector('input[id^="current-user-"]').value;
                const isCurrentUser = user === currentUser;
                const messageDiv = document.createElement('div');
                messageDiv.className = `mb-2 ${isCurrentUser ? 'text-end' : ''}`;
                messageDiv.innerHTML = `
                    <div class="d-inline-block p-2 rounded ${isCurrentUser ? 'bg-primary text-white' : 'bg-light'}">
                        <strong>${user}</strong> <small class="text-muted">(${timestamp})</small><br>
                        ${content}
                    </div>`;
                chatDiv.appendChild(messageDiv);
                chatDiv.scrollTop = chatDiv.scrollHeight;
                console.log('Appended user message:', { user, content, timestamp, room });
            } else {
                console.warn('Chat div not found for room:', room);
            }
        }
    });

    socket.on('error', (data) => {
        console.error('SocketIO error:', data);
        alert(data.msg);
    });

    // Prevent modal from closing during form submission
    document.querySelectorAll('form[data-modal-persist="true"]').forEach(form => {
        const modal = form.closest('.modal');
        if (modal) {
            modal.addEventListener('hide.bs.modal', (e) => {
                if (form.dataset.submitting === 'true') {
                    console.log('Preventing modal close during form submission');
                    e.preventDefault();
                }
            });
        }
    });

    // Handle chat button clicks to join rooms
    document.querySelectorAll('.chat-btn').forEach(button => {
        button.addEventListener('click', () => {
            const room = button.getAttribute('data-room');
            const rideId = button.getAttribute('data-ride-id');
            const bookingId = button.getAttribute('data-booking-id');
            console.log('Joining room:', room, { rideId, bookingId });
            socket.emit('join', {
                room: room,
                ride_id: rideId ? parseInt(rideId) : null,
                booking_id: bookingId ? parseInt(bookingId) : null
            });
        });
    });

    // Handle modal close to leave rooms
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('hidden.bs.modal', () => {
            const chatDiv = modal.querySelector('div[id^="chat-messages-"]');
            if (chatDiv) {
                const [_, type, id] = chatDiv.id.split('-');
                const room = `${type}-${id}`;
                console.log('Leaving room:', room);
                socket.emit('leave', { room: room });
            }
        });
    });

    // Handle modal show to rejoin room and scroll
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('shown.bs.modal', () => {
            const chatDiv = modal.querySelector('div[id^="chat-messages-"]');
            if (chatDiv) {
                const [_, type, id] = chatDiv.id.split('-');
                const room = `${type}-${id}`;
                console.log('Modal shown, rejoining room:', room);
                socket.emit('join', {
                    room: room,
                    ride_id: type === 'ride' ? parseInt(id) : null,
                    booking_id: type === 'booking' ? parseInt(id) : null
                });
                chatDiv.scrollTop = chatDiv.scrollHeight;
            }
        });
    });

    // Handle chat forms for rides
    document.querySelectorAll('form[id^="chat-form-ride-"]').forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Ride chat form submitted');
            try {
                const input = form.querySelector('input[id^="chat-input-ride-"]');
                const sendBtn = form.querySelector('button[id^="send-btn-ride-"]');
                const rideId = form.id.split('-').pop();
                const message = input.value.trim();
                const currentUser = form.querySelector('input[id^="current-user-"]').value;
                form.dataset.submitting = 'true';
                if (message) {
                    console.log('Sending message for ride:', rideId, 'Content:', message, 'User:', currentUser);
                    sendBtn.disabled = true;
                    sendBtn.textContent = 'Sending...';
                    socket.emit('send_message', {
                        room: `ride-${rideId}`,
                        message: message,
                        ride_id: parseInt(rideId),
                        user: currentUser
                    }, () => {
                        console.log('Message sent callback for ride:', rideId);
                    });
                    input.value = '';
                    setTimeout(() => {
                        sendBtn.disabled = false;
                        sendBtn.textContent = 'Send';
                        form.dataset.submitting = 'false';
                    }, 500);
                } else {
                    console.log('Empty message, not sending');
                    form.dataset.submitting = 'false';
                }
            } catch (error) {
                console.error('Error in ride chat form submission:', error);
                form.dataset.submitting = 'false';
                alert('Failed to send message. Please try again.');
            }
        });
    });

    // Handle chat forms for bookings
    document.querySelectorAll('form[id^="chat-form-booking-"]').forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Booking chat form submitted');
            try {
                const input = form.querySelector('input[id^="chat-input-booking-"]');
                const sendBtn = form.querySelector('button[id^="send-btn-booking-"]');
                const bookingId = form.id.split('-').pop();
                const message = input.value.trim();
                const currentUser = form.querySelector('input[id^="current-user-"]').value;
                form.dataset.submitting = 'true';
                if (message) {
                    console.log('Sending message for booking:', bookingId, 'Content:', message, 'User:', currentUser);
                    sendBtn.disabled = true;
                    sendBtn.textContent = 'Sending...';
                    socket.emit('send_message', {
                        room: `booking-${bookingId}`,
                        message: message,
                        booking_id: parseInt(bookingId),
                        user: currentUser
                    }, () => {
                        console.log('Message sent callback for booking:', bookingId);
                    });
                    input.value = '';
                    setTimeout(() => {
                        sendBtn.disabled = false;
                        sendBtn.textContent = 'Send';
                        form.dataset.submitting = 'false';
                    }, 500);
                } else {
                    console.log('Empty message, not sending');
                    form.dataset.submitting = 'false';
                }
            } catch (error) {
                console.error('Error in booking chat form submission:', error);
                form.dataset.submitting = 'false';
                alert('Failed to send message. Please try again.');
            }
        });
    });
});