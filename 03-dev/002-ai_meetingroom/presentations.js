// 演示文稿数据
const presentations = [
    {
        id: 'project-update',
        title: '项目进度汇报',
        content: `
            <div style="text-align: center;">
                <h2>AI开发团队项目进度汇报</h2>
                <br>
                <div style="text-align: left; margin: 0 auto; width: 80%;">
                    <h3>本周完成的工作：</h3>
                    <ul>
                        <li>前端React组件开发完成</li>
                        <li>后端API接口实现</li>
                        <li>数据库设计优化</li>
                        <li>CI/CD流水线配置</li>
                    </ul>
                    <br>
                    <h3>下周计划：</h3>
                    <ul>
                        <li>系统集成测试</li>
                        <li>性能优化</li>
                        <li>用户文档编写</li>
                        <li>部署生产环境</li>
                    </ul>
                </div>
            </div>
        `
    },
    {
        id: 'technical-design',
        title: '技术架构设计',
        content: `
            <div style="text-align: center;">
                <h2>系统技术架构设计</h2>
                <br>
                <div style="text-align: left; margin: 0 auto; width: 80%;">
                    <h3>架构分层：</h3>
                    <ol>
                        <li>前端层：React + TypeScript</li>
                        <li>API层：FastAPI</li>
                        <li>业务逻辑层：Python</li>
                        <li>数据访问层：SQLAlchemy</li>
                        <li>数据库层：PostgreSQL</li>
                    </ol>
                    <br>
                    <h3>技术栈选择：</h3>
                    <ul>
                        <li>前端：React 18, TypeScript, Tailwind CSS</li>
                        <li>后端：FastAPI, Python 3.9+, Redis</li>
                        <li>部署：Docker, Kubernetes, Nginx</li>
                    </ul>
                </div>
            </div>
        `
    },
    {
        id: 'testing-plan',
        title: '测试计划',
        content: `
            <div style="text-align: center;">
                <h2>系统测试计划</h2>
                <br>
                <div style="text-align: left; margin: 0 auto; width: 80%;">
                    <h3>测试类型：</h3>
                    <ul>
                        <li>单元测试：覆盖率 ≥ 80%</li>
                        <li>集成测试：接口测试</li>
                        <li>系统测试：功能测试</li>
                        <li>性能测试：压力测试</li>
                        <li>安全测试：漏洞扫描</li>
                    </ul>
                    <br>
                    <h3>测试工具：</h3>
                    <ul>
                        <li>Jest：前端单元测试</li>
                        <li>Pytest：后端单元测试</li>
                        <li>Postman：API测试</li>
                        <li>JMeter：性能测试</li>
                    </ul>
                </div>
            </div>
        `
    }
];

module.exports = presentations;