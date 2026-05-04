// 히스토리 필터링 및 정렬 기능

let currentFilter = 'all';
let currentSort = 'date-desc';

// 필터 적용
function filterHistory(filterValue) {
    currentFilter = filterValue;

    const cards = document.querySelectorAll('.business-card');
    const filterTabs = document.querySelectorAll('.filter-tab');

    // 탭 활성화 상태 변경
    filterTabs.forEach(tab => {
        if (tab.getAttribute('data-filter') === filterValue) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // 카드 필터링
    let visibleCount = 0;
    cards.forEach(card => {
        const priority = card.getAttribute('data-priority');
        const match = filterValue === 'all' || priority === filterValue;

        if (match) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // 결과 없음 메시지
    const existingEmpty = document.getElementById('filter-empty-msg');
    if (existingEmpty) existingEmpty.remove();

    if (visibleCount === 0) {
        const labelMap = { '1': '1순위', '2': '2순위', 'pass': '패스' };
        const label = labelMap[filterValue] || filterValue;
        const emptyMsg = document.createElement('div');
        emptyMsg.id = 'filter-empty-msg';
        emptyMsg.className = 'bg-white rounded-2xl shadow-lg p-10 text-center text-gray-500';
        emptyMsg.innerHTML = `<p class="text-lg font-semibold mb-1">${label} 업체가 없습니다</p><p class="text-sm">다른 필터를 선택하거나 진단을 먼저 진행해 주세요.</p>`;
        const historyContainer = document.getElementById('historyContainer');
        if (historyContainer) historyContainer.appendChild(emptyMsg);
    }

    // 정렬 재적용
    sortHistory(currentSort);
}

// 정렬 적용
function sortHistory(sortValue) {
    currentSort = sortValue;

    const container = document.getElementById('historyContainer');
    const cards = Array.from(document.querySelectorAll('.business-card'));

    // 보이는 카드만 정렬
    const visibleCards = cards.filter(card => card.style.display !== 'none');

    visibleCards.sort((a, b) => {
        switch (sortValue) {
            case 'date-desc':
                return parseFloat(b.getAttribute('data-date')) - parseFloat(a.getAttribute('data-date'));
            case 'date-asc':
                return parseFloat(a.getAttribute('data-date')) - parseFloat(b.getAttribute('data-date'));
            case 'score-desc':
                return parseInt(b.getAttribute('data-score')) - parseInt(a.getAttribute('data-score'));
            case 'score-asc':
                return parseInt(a.getAttribute('data-score')) - parseInt(b.getAttribute('data-score'));
            default:
                return 0;
        }
    });

    // DOM 재정렬 (빈 상태 메시지는 제외하고 업체 카드만 정렬)
    visibleCards.forEach(card => {
        container.appendChild(card);
    });

    // 빈 상태 메시지는 항상 마지막으로 이동
    const emptyMsg = document.getElementById('filter-empty-msg');
    if (emptyMsg) container.appendChild(emptyMsg);
}

// 통계 계산 및 업데이트
function updateStatistics() {
    const cards = document.querySelectorAll('.business-card');

    let count1 = 0;
    let count2 = 0;
    let countPass = 0;
    let totalScore = 0;
    let scoreCount = 0;

    cards.forEach(card => {
        const priority = card.getAttribute('data-priority');
        const score = parseInt(card.getAttribute('data-score'));

        if (priority === '1') count1++;
        else if (priority === '2') count2++;
        else countPass++;

        if (!isNaN(score)) {
            totalScore += score;
            scoreCount++;
        }
    });

    // 카운트 업데이트
    document.getElementById('count-all').textContent = `(${cards.length})`;
    document.getElementById('count-1').textContent = `(${count1})`;
    document.getElementById('count-2').textContent = `(${count2})`;
    document.getElementById('count-pass').textContent = `(${countPass})`;

    // 통계 요약 업데이트
    const stat1 = document.getElementById('stat-priority-1');
    const stat2 = document.getElementById('stat-priority-2');
    const statAvgScore = document.getElementById('stat-avg-score');

    if (stat1) stat1.textContent = count1;
    if (stat2) stat2.textContent = count2;
    if (statAvgScore && scoreCount > 0) {
        statAvgScore.textContent = Math.round(totalScore / scoreCount);
    }
}

// 영업 단계 업데이트 (localStorage에 임시 저장)
function updateSalesStage(historyId, stage) {
    // localStorage 키: sales_stage_{historyId}
    const key = `sales_stage_${historyId}`;
    localStorage.setItem(key, stage);

    // 시각적 피드백 (토스트 메시지)
    showStageUpdateToast(`영업 단계가 '${stage}'로 변경되었습니다.`);
}

// 영업 단계 가져오기 (저장된 값 또는 기본값)
function getSalesStage(historyId, defaultValue) {
    const key = `sales_stage_${historyId}`;
    return localStorage.getItem(key) || defaultValue || '미접촉';
}

// 토스트 알림 (영업 단계 변경 시)
function showStageUpdateToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-blue-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50';
    toast.innerHTML = `
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
        </svg>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);

    // 2초 후 제거
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', () => {
    updateStatistics();

    // URL 해시에 메시지 앵커가 있으면 스크롤
    if (window.location.hash === '#messages') {
        setTimeout(() => {
            const messagesSection = document.querySelector('.message-tabs');
            if (messagesSection) {
                messagesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 300);
    }
});
