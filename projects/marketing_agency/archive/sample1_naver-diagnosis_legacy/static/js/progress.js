// Progress polling for loading page
let pollInterval = null;
let pollTimeout = null;
const MAX_POLL_TIME = 5 * 60 * 1000; // 5 minutes

const STATUS_CONFIG = {
    searching: {
        progress: 20,
        text: '네이버 플레이스 검색 중...',
        step: 'step-searching'
    },
    crawling: {
        progress: 50,
        text: '업체 정보 수집 중...',
        step: 'step-crawling'
    },
    analyzing: {
        progress: 75,
        text: '진단 점수 산출 중...',
        step: 'step-analyzing'
    },
    generating: {
        progress: 90,
        text: 'PPT 제안서 생성 중...',
        step: 'step-generating'
    },
    done: {
        progress: 100,
        text: '완료!',
        step: null
    }
};

function startProgressPolling(jobId) {
    const startTime = Date.now();

    // Set timeout to prevent infinite polling
    pollTimeout = setTimeout(() => {
        stopPolling();
        window.location.href = `/error?message=${encodeURIComponent('진단 시간이 초과되었습니다. 다시 시도해주세요.')}&error_type=crawl_failed`;
    }, MAX_POLL_TIME);

    // Start polling every 1 second
    pollInterval = setInterval(() => {
        pollStatus(jobId);
    }, 1000);

    // Initial poll
    pollStatus(jobId);
}

async function pollStatus(jobId) {
    try {
        const response = await fetch(`/crawl/status/${jobId}`);

        if (!response.ok) {
            throw new Error('Failed to fetch status');
        }

        const data = await response.json();

        // Update UI
        updateProgress(data.status, data.progress || 0);

        // Handle completion
        if (data.status === 'done' && data.result_id) {
            stopPolling();
            // Small delay for UX
            setTimeout(() => {
                window.location.href = `/result/${data.result_id}`;
            }, 500);
        } else if (data.status === 'failed') {
            stopPolling();
            const errorMsg = data.error_message || '진단 처리 중 오류가 발생했습니다.';
            window.location.href = `/error?message=${encodeURIComponent(errorMsg)}&error_type=crawl_failed`;
        }
    } catch (error) {
        console.error('Poll error:', error);
        // Continue polling on error (network issues, etc.)
    }
}

function updateProgress(status, progress) {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.searching;
    const actualProgress = progress || config.progress;

    // Update percentage text
    const percentElement = document.getElementById('progressPercent');
    if (percentElement) {
        percentElement.textContent = `${actualProgress}%`;
    }

    // Update status text
    const statusElement = document.getElementById('statusText');
    if (statusElement) {
        statusElement.textContent = config.text;
    }

    // Update circular progress bar
    updateCircularProgress(actualProgress);

    // Update step highlights
    updateStepHighlights(status);
}

function updateCircularProgress(percent) {
    const circle = document.getElementById('progressCircle');
    if (!circle) return;

    const radius = 90;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percent / 100) * circumference;

    circle.style.strokeDashoffset = offset;

    // Change color based on progress
    if (percent >= 100) {
        circle.style.stroke = '#10B981'; // green
    } else if (percent >= 75) {
        circle.style.stroke = '#0066FF'; // blue
    } else if (percent >= 50) {
        circle.style.stroke = '#3B82F6'; // lighter blue
    }
}

function updateStepHighlights(status) {
    // Reset all steps
    document.querySelectorAll('.step-item').forEach(step => {
        step.classList.remove('bg-blue-50', 'bg-green-50');
        step.classList.add('bg-gray-50');

        const icon = step.querySelector('.step-icon');
        icon.classList.remove('bg-blue-500', 'bg-green-500');
        icon.classList.add('bg-gray-200');

        const svg = icon.querySelector('svg');
        svg.classList.remove('text-white', 'text-blue-600', 'text-green-600');
        svg.classList.add('text-gray-500');
    });

    // Highlight completed and current steps
    const steps = ['searching', 'crawling', 'analyzing', 'generating'];
    const currentIndex = steps.indexOf(status);

    steps.forEach((stepName, index) => {
        const stepElement = document.getElementById(`step-${stepName}`);
        if (!stepElement) return;

        const icon = stepElement.querySelector('.step-icon');
        const svg = icon.querySelector('svg');

        if (index < currentIndex) {
            // Completed steps
            stepElement.classList.remove('bg-gray-50');
            stepElement.classList.add('bg-green-50');
            icon.classList.remove('bg-gray-200');
            icon.classList.add('bg-green-500');
            svg.classList.remove('text-gray-500');
            svg.classList.add('text-white');
        } else if (index === currentIndex) {
            // Current step
            stepElement.classList.remove('bg-gray-50');
            stepElement.classList.add('bg-blue-50');
            icon.classList.remove('bg-gray-200');
            icon.classList.add('bg-blue-500');
            svg.classList.remove('text-gray-500');
            svg.classList.add('text-white');
        }
    });
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    if (pollTimeout) {
        clearTimeout(pollTimeout);
        pollTimeout = null;
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', stopPolling);
