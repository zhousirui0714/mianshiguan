/**
 * 首页学习数据看板 — 图表初始化
 * 依赖: Chart.js (CDN)
 */

// Chart.js 全局注册
(function () {
    // 等待 Chart.js 加载
    var checkChart = setInterval(function () {
        if (typeof Chart !== 'undefined') {
            clearInterval(checkChart);
            initCharts();
        }
    }, 200);

    // 超时处理
    setTimeout(function () {
        clearInterval(checkChart);
    }, 10000);

    // 暗色主题默认配置
    Chart.defaults.color = '#94A3B8';
    Chart.defaults.borderColor = 'rgba(148, 163, 184, 0.1)';

    /**
     * 初始化雷达图
     * @param {HTMLElement} canvas
     * @param {Array} dimensions - [{name, score, max_score}]
     */
    window.initRadarChart = function (canvas, dimensions) {
        if (!canvas) return;
        if (!dimensions || dimensions.length === 0) {
            dimensions = [
                {name: '逻辑表达', score: 0},
                {name: '沟通能力', score: 0},
                {name: '应变能力', score: 0},
                {name: '专业知识', score: 0},
                {name: '结构化回答', score: 0}
            ];
        }

        if (canvas.chartInstance) {
            canvas.chartInstance.destroy();
        }

        var ctx = canvas.getContext('2d');
        canvas.chartInstance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: dimensions.map(function (d) { return d.name; }),
                datasets: [{
                    label: '能力评分',
                    data: dimensions.map(function (d) { return d.score; }),
                    backgroundColor: 'rgba(125, 211, 252, 0.12)',
                    borderColor: '#7DD3FC',
                    borderWidth: 2,
                    pointBackgroundColor: '#7DD3FC',
                    pointBorderColor: 'rgba(255,255,255,0.3)',
                    pointBorderWidth: 1,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#F8FAFC',
                        bodyColor: '#94A3B8',
                        borderColor: 'rgba(56, 189, 248, 0.2)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: function (context) {
                                return context.parsed.r + ' / 100';
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            color: 'rgba(148, 163, 184, 0.4)',
                            backdropColor: 'transparent',
                            font: { size: 10 }
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)',
                        },
                        angleLines: {
                            color: 'rgba(148, 163, 184, 0.1)',
                        },
                        pointLabels: {
                            color: '#F8FAFC',
                            font: {
                                size: 12,
                                weight: '500',
                                family: '-apple-system, PingFang SC, Microsoft YaHei, sans-serif'
                            }
                        }
                    }
                }
            }
        });
    };

    /**
     * 初始化得分趋势折线图
     * @param {HTMLElement} canvas
     * @param {Array} scores - [{date, score}]
     */
    window.initTrendChart = function (canvas, scores) {
        if (!canvas) return;
        if (!scores || scores.length === 0) {
            scores = [{date: new Date().toISOString().slice(0,10), score: 0}];
        }

        if (canvas.chartInstance) {
            canvas.chartInstance.destroy();
        }

        var labels = scores.map(function (s, i) { return '#' + (i + 1); });
        var values = scores.map(function (s) { return s.score; });

        // 渐变填充
        var ctx = canvas.getContext('2d');
        var gradient = ctx.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, 'rgba(56, 189, 248, 0.25)');
        gradient.addColorStop(1, 'rgba(56, 189, 248, 0.01)');

        canvas.chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '得分',
                    data: values,
                    borderColor: '#38BDF8',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#38BDF8',
                    pointBorderColor: 'rgba(15, 23, 42, 0.8)',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#F8FAFC',
                        bodyColor: '#94A3B8',
                        borderColor: 'rgba(56, 189, 248, 0.2)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: function (context) {
                                return '得分: ' + context.parsed.y;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(148, 163, 184, 0.06)',
                            drawBorder: false,
                        },
                        ticks: {
                            color: 'rgba(148, 163, 184, 0.5)',
                            font: { size: 11 }
                        }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        grid: {
                            color: 'rgba(148, 163, 184, 0.06)',
                            drawBorder: false,
                        },
                        ticks: {
                            color: 'rgba(148, 163, 184, 0.5)',
                            font: { size: 11 },
                            stepSize: 25,
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    };

    /**
     * 销毁所有图表
     */
    window.destroyDashboardCharts = function () {
        document.querySelectorAll('canvas').forEach(function (c) {
            if (c.chartInstance) {
                c.chartInstance.destroy();
                c.chartInstance = null;
            }
        });
    };

    function initCharts() {
        // Chart.js 已加载，可以安全使用
        console.log('[Dashboard] Chart.js ready');
    }
})();
