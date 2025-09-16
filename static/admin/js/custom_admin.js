// Custom Django Admin JavaScript for DigitalBoda
// Enhanced interactivity and user experience

(function($) {
    'use strict';

    // Wait for Django admin to load
    $(document).ready(function() {
        
        // Initialize all custom features
        initializeCustomFeatures();
        initializeStatsCards();
        initializeInteractiveElements();
        initializeFormEnhancements();
        initializeNotifications();
    });

    function initializeCustomFeatures() {
        // Add custom CSS class to body for styling
        $('body').addClass('digitalboda-admin');
        
        // Add loading states to buttons
        $('input[type="submit"], .button').on('click', function() {
            const $btn = $(this);
            const originalText = $btn.val() || $btn.text();
            
            $btn.prop('disabled', true);
            if ($btn.is('input')) {
                $btn.val('Processing...');
            } else {
                $btn.html('<span class="loading-spinner"></span> Processing...');
            }
            
            // Re-enable after 3 seconds if not redirected
            setTimeout(function() {
                $btn.prop('disabled', false);
                if ($btn.is('input')) {
                    $btn.val(originalText);
                } else {
                    $btn.text(originalText);
                }
            }, 3000);
        });

        // Enhanced search functionality
        const $searchInput = $('#toolbar input[type="text"]');
        if ($searchInput.length) {
            $searchInput.attr('placeholder', 'Search riders, sessions, stages...');
            
            // Add search suggestions (mock implementation)
            $searchInput.on('focus', function() {
                $(this).addClass('search-focused');
            }).on('blur', function() {
                $(this).removeClass('search-focused');
            });
        }

        // Add confirmation dialogs for delete actions
        $('.deletelink, .deletelink-box').on('click', function(e) {
            const confirmed = confirm('Are you sure you want to delete this item? This action cannot be undone.');
            if (!confirmed) {
                e.preventDefault();
                return false;
            }
        });

        // Add bulk action confirmations
        $('select[name="action"]').on('change', function() {
            const action = $(this).val();
            if (action && action.includes('delete')) {
                $(this).addClass('danger-action');
            } else {
                $(this).removeClass('danger-action');
            }
        });
    }

    function initializeStatsCards() {
        // Create stats dashboard if on main admin page
        if ($('body').hasClass('dashboard')) {
            createStatsDashboard();
        }

        // Add real-time stats updates
        if (typeof(EventSource) !== "undefined") {
            // This would connect to a real-time stats endpoint
            // For now, we'll simulate with periodic updates
            setInterval(updateStats, 30000); // Update every 30 seconds
        }
    }

    function createStatsDashboard() {
        const $content = $('#content-main');
        const statsHtml = `
            <div class="stats-container">
                <div class="stats-card icon-riders">
                    <h3 id="total-riders">Loading...</h3>
                    <p>Total Riders</p>
                </div>
                <div class="stats-card icon-training">
                    <h3 id="active-sessions">Loading...</h3>
                    <p>Active Sessions</p>
                </div>
                <div class="stats-card icon-attendance">
                    <h3 id="attendance-rate">Loading...</h3>
                    <p>Attendance Rate</p>
                </div>
                <div class="stats-card icon-stages">
                    <h3 id="active-stages">Loading...</h3>
                    <p>Active Stages</p>
                </div>
            </div>
        `;
        
        $content.prepend(statsHtml);
        
        // Load initial stats
        loadDashboardStats();
    }

    function loadDashboardStats() {
        // Mock data - in real implementation, this would be AJAX calls
        $('#total-riders').text('245');
        $('#active-sessions').text('12');
        $('#attendance-rate').text('87%');
        $('#active-stages').text('18');
        
        // Animate numbers counting up
        animateNumbers();
    }

    function animateNumbers() {
        $('.stats-card h3').each(function() {
            const $this = $(this);
            const finalValue = parseInt($this.text()) || 0;
            const duration = 2000;
            const increment = finalValue / (duration / 50);
            let currentValue = 0;
            
            const timer = setInterval(function() {
                currentValue += increment;
                if (currentValue >= finalValue) {
                    clearInterval(timer);
                    $this.text(finalValue + ($this.text().includes('%') ? '%' : ''));
                } else {
                    $this.text(Math.floor(currentValue));
                }
            }, 50);
        });
    }

    function updateStats() {
        // This would make AJAX calls to get updated stats
        console.log('Updating stats...');
        
        // Mock update - randomly change some numbers slightly
        const $riders = $('#total-riders');
        if ($riders.length) {
            const current = parseInt($riders.text()) || 0;
            const change = Math.floor(Math.random() * 5) - 2; // -2 to +2
            const newValue = Math.max(0, current + change);
            $riders.text(newValue);
        }
    }

    function initializeInteractiveElements() {
        // Add hover effects to table rows
        $('#result_list tbody tr').on('mouseenter', function() {
            $(this).addClass('row-highlight');
        }).on('mouseleave', function() {
            $(this).removeClass('row-highlight');
        });

        // Add progress bars for completion percentages
        $('.completion-percentage').each(function() {
            const $this = $(this);
            const percentage = parseInt($this.text()) || 0;
            const progressBar = `
                <div class="progress-bar">
                    <div class="progress-bar-fill" style="width: ${percentage}%"></div>
                </div>
                <small>${percentage}%</small>
            `;
            $this.html(progressBar);
        });

        // Add status badges
        $('.status-field').each(function() {
            const $this = $(this);
            const status = $this.text().toLowerCase().trim();
            $this.addClass('status-badge');
            
            if (status.includes('active') || status.includes('approved') || status.includes('completed')) {
                $this.addClass('status-active');
            } else if (status.includes('pending') || status.includes('scheduled')) {
                $this.addClass('status-pending');
            } else if (status.includes('inactive') || status.includes('cancelled') || status.includes('rejected')) {
                $this.addClass('status-inactive');
            } else {
                $this.addClass('status-completed');
            }
        });

        // Add tooltips to abbreviated fields
        $('[title]').tooltip({
            placement: 'top',
            trigger: 'hover'
        });

        // Add quick actions menu
        $('#result_list tbody tr').each(function() {
            const $row = $(this);
            const $actions = $row.find('.action-checkbox-column');
            
            if ($actions.length) {
                const quickActionsHtml = `
                    <div class="quick-actions" style="display: none;">
                        <button class="btn-quick-edit" title="Quick Edit">✏️</button>
                        <button class="btn-quick-view" title="View Details">👁️</button>
                        <button class="btn-quick-delete" title="Delete">🗑️</button>
                    </div>
                `;
                $actions.append(quickActionsHtml);
            }
        });

        // Show/hide quick actions on row hover
        $('#result_list tbody tr').on('mouseenter', function() {
            $(this).find('.quick-actions').slideDown(200);
        }).on('mouseleave', function() {
            $(this).find('.quick-actions').slideUp(200);
        });
    }

    function initializeFormEnhancements() {
        // Add character counters to text areas
        $('textarea[maxlength]').each(function() {
            const $textarea = $(this);
            const maxLength = $textarea.attr('maxlength');
            const counter = $(`<div class="char-counter">${$textarea.val().length}/${maxLength}</div>`);
            
            $textarea.after(counter);
            
            $textarea.on('input', function() {
                const currentLength = $(this).val().length;
                counter.text(`${currentLength}/${maxLength}`);
                
                if (currentLength > maxLength * 0.9) {
                    counter.addClass('warning');
                } else {
                    counter.removeClass('warning');
                }
            });
        });

        // Add form validation indicators
        $('input[required], select[required], textarea[required]').each(function() {
            $(this).addClass('required-field');
        });

        // Auto-save draft functionality
        let autoSaveTimer;
        $('form').on('input', 'input, textarea, select', function() {
            clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(function() {
                saveDraft();
            }, 2000);
        });

        // Add field dependencies (show/hide based on other field values)
        initializeFieldDependencies();

        // Add inline editing for simple fields
        $('.editable-field').on('dblclick', function() {
            const $field = $(this);
            const currentValue = $field.text();
            const input = $(`<input type="text" value="${currentValue}" class="inline-edit">`);
            
            $field.html(input);
            input.focus().select();
            
            input.on('blur', function() {
                const newValue = $(this).val();
                $field.text(newValue);
                // Here you would make an AJAX call to save the change
            });
        });
    }

    function initializeFieldDependencies() {
        // Example: Show location fields only when status is 'ACTIVE'
        $('select[name="status"]').on('change', function() {
            const status = $(this).val();
            const $locationFields = $('.field-location, .field-gps_latitude, .field-gps_longitude');
            
            if (status === 'ACTIVE') {
                $locationFields.slideDown();
            } else {
                $locationFields.slideUp();
            }
        }).trigger('change');

        // Show trainer fields only when session is scheduled
        $('select[name="session_type"]').on('change', function() {
            const sessionType = $(this).val();
            const $trainerFields = $('.field-trainer, .field-scheduled_date');
            
            if (sessionType === 'SCHEDULED') {
                $trainerFields.slideDown();
            } else {
                $trainerFields.slideUp();
            }
        }).trigger('change');
    }

    function saveDraft() {
        // Mock implementation - would save form data to localStorage or server
        console.log('Auto-saving draft...');
        
        const formData = $('form').serialize();
        localStorage.setItem('admin_form_draft', formData);
        
        // Show save indicator
        showNotification('Draft saved', 'info', 2000);
    }

    function initializeNotifications() {
        // Create notification container
        if (!$('#notification-container').length) {
            $('body').append('<div id="notification-container"></div>');
        }

        // Add notification styles
        const notificationStyles = `
            <style>
                #notification-container {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10000;
                    max-width: 300px;
                }
                .notification {
                    background: white;
                    border-left: 4px solid #4CA1AF;
                    border-radius: 4px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    margin-bottom: 10px;
                    padding: 15px;
                    animation: slideIn 0.3s ease;
                }
                .notification.success { border-left-color: #27AE60; }
                .notification.error { border-left-color: #E74C3C; }
                .notification.warning { border-left-color: #F39C12; }
                .notification.info { border-left-color: #3498DB; }
                
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                
                .loading-spinner {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border: 2px solid #f3f3f3;
                    border-top: 2px solid #4CA1AF;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
            </style>
        `;
        $('head').append(notificationStyles);

        // Check for Django messages and convert them to notifications
        $('.messagelist li').each(function() {
            const $msg = $(this);
            const type = $msg.attr('class');
            const text = $msg.text();
            
            showNotification(text, type, 5000);
            $msg.hide();
        });
    }

    function showNotification(message, type = 'info', duration = 5000) {
        const notification = $(`
            <div class="notification ${type}">
                ${message}
            </div>
        `);
        
        $('#notification-container').append(notification);
        
        if (duration > 0) {
            setTimeout(function() {
                notification.fadeOut(300, function() {
                    $(this).remove();
                });
            }, duration);
        }
    }

    // Add keyboard shortcuts
    $(document).on('keydown', function(e) {
        // Ctrl+S or Cmd+S to save form
        if ((e.ctrlKey || e.metaKey) && e.keyCode === 83) {
            e.preventDefault();
            $('input[type="submit"], .submit-row input').first().click();
            return false;
        }
        
        // Escape to close modals or cancel inline editing
        if (e.keyCode === 27) {
            $('.inline-edit').blur();
            $('.modal').hide();
        }
    });

    // Add search filtering for long lists
    if ($('#result_list tbody tr').length > 20) {
        addQuickSearch();
    }

    function addQuickSearch() {
        const searchHtml = `
            <div class="quick-search" style="margin: 10px 0;">
                <input type="text" id="quick-search" placeholder="Quick search in results..." 
                       style="width: 300px; padding: 8px; border: 1px solid #4CA1AF; border-radius: 4px;">
                <button type="button" id="clear-search" style="margin-left: 5px; padding: 8px;">Clear</button>
            </div>
        `;
        
        $('#result_list').before(searchHtml);
        
        $('#quick-search').on('input', function() {
            const searchTerm = $(this).val().toLowerCase();
            
            $('#result_list tbody tr').each(function() {
                const rowText = $(this).text().toLowerCase();
                if (rowText.includes(searchTerm)) {
                    $(this).show();
                } else {
                    $(this).hide();
                }
            });
        });
        
        $('#clear-search').on('click', function() {
            $('#quick-search').val('');
            $('#result_list tbody tr').show();
        });
    }

    // Export functionality
    if ($('#result_list').length) {
        addExportButton();
    }

    function addExportButton() {
        const exportButton = `
            <button type="button" id="export-data" class="button" style="margin-left: 10px;">
                📊 Export to CSV
            </button>
        `;
        
        $('.actions').append(exportButton);
        
        $('#export-data').on('click', function() {
            exportTableToCSV();
        });
    }

    function exportTableToCSV() {
        const $table = $('#result_list');
        const csv = [];
        
        // Header
        const headers = [];
        $table.find('thead th').each(function() {
            headers.push($(this).text().trim());
        });
        csv.push(headers.join(','));
        
        // Rows
        $table.find('tbody tr:visible').each(function() {
            const row = [];
            $(this).find('td').each(function() {
                let text = $(this).text().trim();
                text = text.replace(/"/g, '""'); // Escape quotes
                row.push(`"${text}"`);
            });
            csv.push(row.join(','));
        });
        
        // Download
        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'digitalboda_data.csv';
        a.click();
        
        window.URL.revokeObjectURL(url);
        
        showNotification('Data exported successfully!', 'success');
    }

    // Global functions for external use
    window.DigitalBodaAdmin = {
        showNotification: showNotification,
        updateStats: updateStats,
        saveDraft: saveDraft
    };

})(django.jQuery);