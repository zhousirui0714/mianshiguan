/**
 * 面试成长伴侣 - API 公共工具
 */

const API = {
    async get(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },

    async post(url, data) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },

    // 场景 API
    scenarios: {
        list: () => API.get('/api/scenarios'),
        get: (id) => API.get(`/api/scenarios/${id}`),
    },

    // 考官 API
    examiner: {
        start: (scenarioId, userId, background) =>
            API.post('/api/examiner/start', {
                scenario_id: scenarioId,
                user_id: userId || 'anonymous',
                user_background: background || '',
            }),
        chat: (convId, scenarioId, message, userId) =>
            API.post('/api/examiner/chat', {
                conversation_id: convId,
                scenario_id: scenarioId,
                user_message: message,
                user_id: userId || 'anonymous',
            }),
        finish: (convId) =>
            API.post('/api/examiner/finish', { conversation_id: convId }),
    },

    // 题库 API
    questions: {
        list: (params) => {
            const qs = new URLSearchParams(params || {}).toString();
            return API.get(`/api/questions${qs ? '?' + qs : ''}`);
        },
    },

    // 用户 API
    user: {
        badges: (userId) => API.get(`/api/user/${userId}/badges`),
        progress: (userId, scenarioId) => {
            const qs = scenarioId ? `?scenario_id=${scenarioId}` : '';
            return API.get(`/api/user/${userId}/progress${qs}`);
        },
    },
};
