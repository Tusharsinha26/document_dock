/**
 * DocumentDock – Interactive Client Script
 * Editorial & Productivity Micro-interactions, Scroll Animations & State Management
 */

document.addEventListener('DOMContentLoaded', () => {

  // ==========================================================================
  // 1. STICKY NAVIGATION & SCROLL PROGRESS
  // ==========================================================================
  const nav = document.querySelector('.site-nav');
  const progressBar = document.getElementById('scrollProgressBar');

  const handleScroll = () => {
    const scrollPos = window.scrollY;
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    if (progressBar && totalHeight > 0) {
      const progressPercent = Math.min((scrollPos / totalHeight) * 100, 100);
      progressBar.style.width = `${progressPercent}%`;
    }

    if (nav) {
      if (scrollPos > 30) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }

      // Parallax effect on hero photo frame
      const heroPhoto = document.querySelector('.hero-photo-frame img');
      if (heroPhoto && scrollPos < 700) {
        heroPhoto.style.transform = `translateY(${scrollPos * 0.07}px) scale(1.02)`;
      }
    }
  };
  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();

  // ==========================================================================
  // 2. MOBILE NAVIGATION DRAWER TOGGLE
  // ==========================================================================
  const navToggleBtn = document.querySelector('.nav-toggle-btn');
  const mobileDrawer = document.querySelector('.mobile-nav-drawer');
  if (navToggleBtn && mobileDrawer) {
    navToggleBtn.addEventListener('click', () => {
      mobileDrawer.classList.toggle('open');
      const isOpen = mobileDrawer.classList.contains('open');
      navToggleBtn.setAttribute('aria-expanded', isOpen);
    });

    mobileDrawer.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        mobileDrawer.classList.remove('open');
      });
    });
  }

  // ==========================================================================
  // 3. DASHBOARD MOBILE SIDEBAR TOGGLE
  // ==========================================================================
  const sidebarToggle = document.querySelector('.sidebar-toggle-btn');
  const appSidebar = document.querySelector('.app-sidebar');
  if (sidebarToggle && appSidebar) {
    sidebarToggle.addEventListener('click', () => {
      appSidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 768 && appSidebar.classList.contains('open')) {
        if (!appSidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
          appSidebar.classList.remove('open');
        }
      }
    });
  }

  // ==========================================================================
  // 4. ANIMATED NUMBER COUNTERS ON SCROLL
  // ==========================================================================
  const counters = document.querySelectorAll('.counter-anim');
  if (counters.length > 0 && 'IntersectionObserver' in window) {
    const counterObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = parseFloat(el.getAttribute('data-target') || '0');
          const isDecimal = el.getAttribute('data-decimal') === 'true';
          const prefix = el.getAttribute('data-prefix') || '';
          const suffix = el.getAttribute('data-suffix') || '';
          const duration = 1400; // ms
          const startTime = performance.now();

          const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const ease = 1 - Math.pow(1 - progress, 3);
            const currentVal = ease * target;

            if (isDecimal) {
              el.textContent = `${prefix}${currentVal.toFixed(1)}${suffix}`;
            } else {
              el.textContent = `${prefix}${Math.floor(currentVal)}${suffix}`;
            }

            if (progress < 1) {
              requestAnimationFrame(updateCounter);
            } else {
              if (isDecimal) {
                el.textContent = `${prefix}${target.toFixed(1)}${suffix}`;
              } else {
                el.textContent = `${prefix}${target}${suffix}`;
              }
            }
          };

          requestAnimationFrame(updateCounter);
          observer.unobserve(el);
        }
      });
    }, { threshold: 0.2 });

    counters.forEach(c => counterObserver.observe(c));
  }

  // ==========================================================================
  // 5. MAGNETIC 3D TILT EFFECT ON HERO CARDS & FEATURE CARDS
  // ==========================================================================
  const tiltElements = document.querySelectorAll('.hero-floating-card, .editorial-story-card, .testimonial-card');
  tiltElements.forEach(el => {
    el.addEventListener('mousemove', (e) => {
      const rect = el.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const rotateX = ((y - centerY) / centerY) * -5;
      const rotateY = ((x - centerX) / centerX) * 5;

      el.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
    });

    el.addEventListener('mouseleave', () => {
      el.style.transform = '';
    });
  });

  // ==========================================================================
  // 6. INTERACTIVE FAQ ACCORDION
  // ==========================================================================
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach(item => {
    const btn = item.querySelector('.faq-question-btn');
    if (btn) {
      btn.addEventListener('click', () => {
        const isOpen = item.classList.contains('open');
        // Close siblings
        faqItems.forEach(other => {
          if (other !== item) other.classList.remove('open');
        });
        item.classList.toggle('open', !isOpen);
      });
    }
  });

  // ==========================================================================
  // 7. INTERACTIVE EXPIRY SIMULATOR / CALCULATOR
  // ==========================================================================
  const simType = document.getElementById('simDocType');
  const simMonths = document.getElementById('simMonthsRemaining');
  const simOutputBox = document.getElementById('simOutputBox');
  const simStatusBadge = document.getElementById('simStatusBadge');
  const simHeadline = document.getElementById('simHeadline');
  const simAdvice = document.getElementById('simAdvice');

  if (simType && simMonths && simOutputBox) {
    const calculateSimulation = () => {
      const type = simType.value;
      const months = parseInt(simMonths.value, 10);

      if (type === 'passport') {
        if (months <= 6) {
          simStatusBadge.className = 'status-pill status-expired';
          simStatusBadge.textContent = 'CRITICAL TRAVEL RESTRICTION';
          simHeadline.textContent = `High Risk: ${months} Months Remaining`;
          simAdvice.textContent = 'Over 70 international jurisdictions (including Schengen Area, Thailand, Indonesia) enforce a mandatory 6-month validity threshold. You are likely ineligible to board international flights.';
        } else if (months <= 9) {
          simStatusBadge.className = 'status-pill status-warning';
          simStatusBadge.textContent = 'RENEWAL WINDOW ACTIVE';
          simHeadline.textContent = `Action Recommended: ${months} Months Remaining`;
          simAdvice.textContent = 'Passport renewals typically take 4 to 8 weeks. Apply now before peak holiday processing backlogs delay your plans.';
        } else {
          simStatusBadge.className = 'status-pill status-active';
          simStatusBadge.textContent = 'HEALTHY STANDING';
          simHeadline.textContent = `Fully Compliant: ${months} Months Remaining`;
          simAdvice.textContent = 'Your passport has sufficient buffer for all global travel. DocumentDock will alert you when you enter the 9-month safety envelope.';
        }
      } else if (type === 'insurance') {
        if (months <= 1) {
          simStatusBadge.className = 'status-pill status-warning';
          simStatusBadge.textContent = 'POLICY EXPIRING IMMINENTLY';
          simHeadline.textContent = `Urgent: ${months} Month Remaining`;
          simAdvice.textContent = 'Request quotes from competitive providers immediately. Avoid automatic rollover rates which average 22% higher than new policy benchmarks.';
        } else {
          simStatusBadge.className = 'status-pill status-active';
          simStatusBadge.textContent = 'COVERAGE ACTIVE';
          simHeadline.textContent = `Active Policy: ${months} Months Remaining`;
          simAdvice.textContent = 'Policy is in good standing. Notice window is set to 30 days prior to direct debit.';
        }
      } else { // tenancy
        if (months <= 2) {
          simStatusBadge.className = 'status-pill status-warning';
          simStatusBadge.textContent = 'BREAK CLAUSE NOTICE TRIGGER';
          simHeadline.textContent = `Notice Deadline: ${months} Months Remaining`;
          simAdvice.textContent = 'Standard residential agreements mandate written notice 60 days before termination. If you miss this date, tenancy locks in for another full term.';
        } else {
          simStatusBadge.className = 'status-pill status-active';
          simStatusBadge.textContent = 'LEASE SECURE';
          simHeadline.textContent = `Fixed Term: ${months} Months Remaining`;
          simAdvice.textContent = 'Enjoy your residency. DocumentDock will monitor the 60-day break clause window.';
        }
      }
    };

    simType.addEventListener('change', calculateSimulation);
    simMonths.addEventListener('input', (e) => {
      const valLabel = document.getElementById('simMonthsVal');
      if (valLabel) valLabel.textContent = `${e.target.value} month${e.target.value > 1 ? 's' : ''}`;
      calculateSimulation();
    });
    calculateSimulation();
  }

  // ==========================================================================
  // 8. INTERACTIVE DASHBOARD PREVIEW TABS (Landing Page)
  // ==========================================================================
  const previewFilterBtns = document.querySelectorAll('.preview-tab-btn');
  const previewRows = document.querySelectorAll('.preview-mock-row');
  if (previewFilterBtns.length > 0 && previewRows.length > 0) {
    previewFilterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        previewFilterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const filter = btn.getAttribute('data-filter');
        previewRows.forEach(row => {
          const rowCategory = row.getAttribute('data-category');
          const rowStatus = row.getAttribute('data-status');

          if (filter === 'all' || rowCategory === filter || rowStatus === filter) {
            row.style.display = '';
            row.style.animation = 'fadeIn 0.3s ease';
          } else {
            row.style.display = 'none';
          }
        });
      });
    });
  }

  // ==========================================================================
  // 9. REAL-TIME FORM LIVE PREVIEW & QUICK DATE HELPERS
  // ==========================================================================
  const formTitleInput = document.querySelector('input[name="title"]');
  const formCatSelect = document.querySelector('select[name="category"]');
  const formNumInput = document.querySelector('input[name="document_number"]');
  const formAuthInput = document.querySelector('input[name="issuing_authority"]');
  const formExpiryInput = document.querySelector('input[name="expiry_date"]');

  const previewTitle = document.getElementById('liveCardTitle');
  const previewCategory = document.getElementById('liveCardCategory');
  const previewNumber = document.getElementById('liveCardNumber');
  const previewIssuer = document.getElementById('liveCardIssuer');
  const previewDelta = document.getElementById('liveCardDelta');

  if (formTitleInput && previewTitle) {
    const updateLiveCard = () => {
      previewTitle.textContent = formTitleInput.value.trim() || 'Untitled Document';
      if (previewCategory && formCatSelect) previewCategory.textContent = formCatSelect.value;
      if (previewNumber && formNumInput) previewNumber.textContent = formNumInput.value.trim() || 'REF: —';
      if (previewIssuer && formAuthInput) previewIssuer.textContent = formAuthInput.value.trim() || 'Issuing body';

      if (previewDelta && formExpiryInput) {
        if (!formExpiryInput.value) {
          previewDelta.textContent = 'Permanent / Lifetime';
          previewDelta.className = 'status-pill status-lifetime';
        } else {
          const expDate = new Date(formExpiryInput.value);
          const today = new Date();
          const diffTime = expDate - today;
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

          if (diffDays < 0) {
            previewDelta.textContent = `Expired ${Math.abs(diffDays)} days ago`;
            previewDelta.className = 'status-pill status-expired';
          } else if (diffDays <= 30) {
            previewDelta.textContent = `Expires in ${diffDays} days`;
            previewDelta.className = 'status-pill status-warning';
          } else {
            previewDelta.textContent = `Valid for ${diffDays} days`;
            previewDelta.className = 'status-pill status-active';
          }
        }
      }
    };

    [formTitleInput, formCatSelect, formNumInput, formAuthInput, formExpiryInput].forEach(inp => {
      if (inp) {
        inp.addEventListener('input', updateLiveCard);
        inp.addEventListener('change', updateLiveCard);
      }
    });
    updateLiveCard();
  }

  // Quick Date Buttons (+1 Year, +5 Years, +10 Years, Lifetime)
  const quickDateBtns = document.querySelectorAll('.quick-date-btn');
  if (quickDateBtns.length > 0 && formExpiryInput) {
    quickDateBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const years = parseInt(btn.getAttribute('data-years') || '0', 10);
        if (years === 0) {
          formExpiryInput.value = '';
        } else {
          const today = new Date();
          today.setFullYear(today.getFullYear() + years);
          const yyyy = today.getFullYear();
          const mm = String(today.getMonth() + 1).padStart(2, '0');
          const dd = String(today.getDate()).padStart(2, '0');
          formExpiryInput.value = `${yyyy}-${mm}-${dd}`;
        }
        formExpiryInput.dispatchEvent(new Event('change'));
      });
    });
  }

  // ==========================================================================
  // 10. FILE DROPZONE UPLOAD PREVIEW
  // ==========================================================================
  const dropzone = document.getElementById('documentDropzone');
  const fileInput = document.getElementById('documentFileInput');
  const dropzonePreview = document.getElementById('dropzonePreview');
  const dropzonePrompt = document.getElementById('dropzonePrompt');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--c-forest)';
        dropzone.style.backgroundColor = 'var(--c-forest-tint)';
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.style.borderColor = '';
        dropzone.style.backgroundColor = '';
      });
    });

    dropzone.addEventListener('drop', (e) => {
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelected(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFileSelected(fileInput.files[0]);
      }
    });

    function handleFileSelected(file) {
      if (!file) return;
      if (dropzonePrompt) dropzonePrompt.style.display = 'none';
      if (dropzonePreview) {
        dropzonePreview.style.display = 'block';
        const nameEl = dropzonePreview.querySelector('.selected-file-name');
        const sizeEl = dropzonePreview.querySelector('.selected-file-size');
        if (nameEl) nameEl.textContent = file.name;
        if (sizeEl) sizeEl.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;

        const imgThumb = dropzonePreview.querySelector('.file-thumb-img');
        if (imgThumb && file.type.startsWith('image/')) {
          const reader = new FileReader();
          reader.onload = (e) => {
            imgThumb.src = e.target.result;
            imgThumb.style.display = 'block';
          };
          reader.readAsDataURL(file);
        }
      }
    }
  }

  // ==========================================================================
  // 11. IMAGE LIGHTBOX MODAL (Detail Page)
  // ==========================================================================
  const lightboxModal = document.getElementById('imageLightboxModal');
  const lightboxImg = document.getElementById('lightboxActiveImage');
  const lightboxTriggers = document.querySelectorAll('.trigger-lightbox');

  if (lightboxModal && lightboxImg && lightboxTriggers.length > 0) {
    lightboxTriggers.forEach(trig => {
      trig.addEventListener('click', (e) => {
        e.preventDefault();
        const src = trig.getAttribute('data-img-src') || trig.getAttribute('src');
        lightboxImg.src = src;
        lightboxModal.classList.add('active');
      });
    });

    const closeBtn = lightboxModal.querySelector('.lightbox-close-btn');
    const closeLightbox = () => {
      lightboxModal.classList.remove('active');
    };

    if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
    lightboxModal.addEventListener('click', (e) => {
      if (e.target === lightboxModal) closeLightbox();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && lightboxModal.classList.contains('active')) {
        closeLightbox();
      }
    });
  }

  // ==========================================================================
  // 12. BESPOKE EDITORIAL CONFIRMATION MODAL (Replaces generic alert)
  // ==========================================================================
  const deleteModal = document.getElementById('editorialDeleteModal');
  const deleteConfirmBtn = document.getElementById('confirmDeleteBtn');
  const deleteTargetTitle = document.getElementById('deleteTargetTitle');
  const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
  let formPendingSubmit = null;

  if (deleteModal) {
    document.querySelectorAll('.btn-confirm-delete').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        formPendingSubmit = btn.closest('form');
        const title = btn.getAttribute('data-title') || 'this document';
        if (deleteTargetTitle) deleteTargetTitle.textContent = title;
        deleteModal.classList.add('active');
      });
    });

    if (cancelDeleteBtn) {
      cancelDeleteBtn.addEventListener('click', () => {
        deleteModal.classList.remove('active');
        formPendingSubmit = null;
      });
    }

    if (deleteConfirmBtn) {
      deleteConfirmBtn.addEventListener('click', () => {
        if (formPendingSubmit) {
          formPendingSubmit.submit();
        }
      });
    }

    deleteModal.addEventListener('click', (e) => {
      if (e.target === deleteModal) {
        deleteModal.classList.remove('active');
        formPendingSubmit = null;
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && deleteModal.classList.contains('active')) {
        deleteModal.classList.remove('active');
        formPendingSubmit = null;
      }
    });
  }

  // ==========================================================================
  // 12B. REAL-TIME CLIENT-SIDE TABLE & GRID INSTANT FILTERING
  // ==========================================================================
  const searchInput = document.getElementById('tableSearchInput');
  const filterableRows = document.querySelectorAll('.filterable-doc-row');
  const emptyNotice = document.getElementById('searchEmptyNotice');

  if (searchInput && filterableRows.length > 0) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      let matchCount = 0;

      filterableRows.forEach(row => {
        const searchCorpus = (row.getAttribute('data-search') || '').toLowerCase();
        if (!query || searchCorpus.includes(query)) {
          row.style.display = '';
          matchCount++;
        } else {
          row.style.display = 'none';
        }
      });

      if (emptyNotice) {
        emptyNotice.style.display = (matchCount === 0 && query.length > 0) ? 'block' : 'none';
      }
    });
  }

  // ==========================================================================
  // 13. GSAP SCROLL ENHANCEMENTS
  // ==========================================================================
  if (window.gsap && window.ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);

    // Fade-in sections with power2.out
    gsap.utils.toArray('.gsap-fade-up').forEach(item => {
      gsap.fromTo(item, 
        { opacity: 0, y: 35 },
        {
          opacity: 1,
          y: 0,
          duration: 0.85,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: item,
            start: 'top 85%',
            toggleActions: 'play none none none'
          }
        }
      );
    });

    // Staggered groups
    gsap.utils.toArray('.gsap-stagger-group').forEach(group => {
      const cards = group.children;
      gsap.fromTo(cards,
        { opacity: 0, y: 30 },
        {
          opacity: 1,
          y: 0,
          duration: 0.7,
          stagger: 0.15,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: group,
            start: 'top 85%'
          }
        }
      );
    });
  }
});
