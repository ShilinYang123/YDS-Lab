/**
 * 长期记忆系统端到端场景测试
 * 
 * @description 测试真实使用场景下的系统行为
 * @author 高级软件专家
 */

import { LongTermMemorySystem } from '../../src';
import type { 
  Agent, 
  Memory, 
  EnhancementContext,
  Task 
} from '../../src/types/base';

describe('长期记忆系统端到端场景测试', () => {
  let memorySystem: LongTermMemorySystem;

  beforeAll(async () => {
    memorySystem = new LongTermMemorySystem();
    await memorySystem.initialize();
  });

  afterAll(async () => {
    await memorySystem.destroy();
  });

  describe('场景1: 智能客服助手学习和改进', () => {
    let customerServiceAgent: Agent;

    beforeEach(() => {
      customerServiceAgent = {
        id: 'customer-service-agent',
        name: 'Customer Service Assistant',
        type: 'customer-service',
        capabilities: [
          'natural-language-understanding',
          'problem-solving',
          'empathy',
          'knowledge-retrieval'
        ],
        knowledge: {
          facts: [
            'Company operates 24/7 customer support',
            'Standard response time is 2 hours',
            'Escalation required for refunds over $500'
          ],
          rules: [
            'Always greet customers politely',
            'Gather all necessary information before providing solutions',
            'Escalate complex technical issues to specialists'
          ],
          procedures: [
            'Customer inquiry handling procedure',
            'Complaint resolution workflow',
            'Product information lookup process'
          ]
        },
        memory: {
          working: [],
          episodic: [],
          semantic: [],
          procedural: []
        },
        performance: {
          successRate: 0.78,
          averageResponseTime: 1200,
          taskCompletionRate: 0.82
        },
        metadata: {
          version: '2.1.0',
          lastUpdated: new Date(),
          specialization: 'customer-service'
        }
      };
    });

    test('应该能够从客户互动中学习并改进响应', async () => {
      // 模拟客户互动历史记忆
      const customerInteractions: Memory[] = [
        {
          id: 'interaction-1',
          type: 'episodic',
          content: 'Customer complained about slow delivery, resolved by providing tracking info and expedited shipping',
          context: {
            customerId: 'cust-001',
            issueType: 'delivery',
            resolution: 'tracking-info-expedited',
            satisfaction: 'high',
            responseTime: 300
          },
          importance: 0.85,
          createdAt: new Date('2024-01-15'),
          updatedAt: new Date('2024-01-15'),
          metadata: {
            tags: ['delivery', 'complaint', 'resolved', 'satisfied'],
            outcome: 'positive'
          }
        },
        {
          id: 'interaction-2',
          type: 'episodic',
          content: 'Customer asked about return policy, provided detailed explanation and initiated return process',
          context: {
            customerId: 'cust-002',
            issueType: 'return',
            resolution: 'policy-explanation-return-initiated',
            satisfaction: 'medium',
            responseTime: 180
          },
          importance: 0.75,
          createdAt: new Date('2024-01-16'),
          updatedAt: new Date('2024-01-16'),
          metadata: {
            tags: ['return', 'policy', 'explanation'],
            outcome: 'neutral'
          }
        },
        {
          id: 'interaction-3',
          type: 'semantic',
          content: 'Customers with delivery issues respond well to proactive communication and compensation offers',
          context: {
            domain: 'customer-service',
            pattern: 'delivery-issue-resolution'
          },
          importance: 0.9,
          createdAt: new Date('2024-01-17'),
          updatedAt: new Date('2024-01-17'),
          metadata: {
            tags: ['delivery', 'communication', 'compensation', 'pattern'],
            source: 'interaction-analysis'
          }
        }
      ];

      // 存储历史互动记忆
      for (const memory of customerInteractions) {
        await memorySystem.storeMemory(memory);
      }

      // 新的客户咨询场景
      const newCustomerTask: Task = {
        type: 'customer-inquiry',
        description: 'Customer is asking about delayed delivery and seems frustrated',
        requirements: [
          'Acknowledge customer frustration',
          'Provide delivery status',
          'Offer appropriate compensation',
          'Ensure customer satisfaction'
        ],
        context: {
          customerId: 'cust-003',
          issueType: 'delivery-delay',
          customerMood: 'frustrated',
          orderValue: 150
        }
      };

      // 使用记忆增强智能体
      const enhancementContext: EnhancementContext = {
        agent: customerServiceAgent,
        task: newCustomerTask,
        environment: {
          platform: 'chat',
          urgency: 'medium'
        }
      };

      const enhancementResult = await memorySystem.enhanceAgent(enhancementContext);

      // 验证增强结果
      expect(enhancementResult.success).toBe(true);
      expect(enhancementResult.enhancedAgent).toBeDefined();
      expect(enhancementResult.appliedMemories.length).toBeGreaterThan(0);

      const enhancedAgent = enhancementResult.enhancedAgent!;

      // 验证智能体学到了相关经验
      expect(enhancedAgent.memory.episodic.length).toBeGreaterThan(0);
      expect(enhancedAgent.memory.semantic.length).toBeGreaterThan(0);

      // 验证性能改进
      expect(enhancedAgent.performance.successRate).toBeGreaterThan(customerServiceAgent.performance.successRate);
      expect(enhancedAgent.performance.averageResponseTime).toBeLessThan(customerServiceAgent.performance.averageResponseTime);

      // 验证应用了相关记忆
      const appliedMemoryIds = enhancementResult.appliedMemories.map(m => m.id);
      expect(appliedMemoryIds).toContain('interaction-1'); // 类似的配送问题
      expect(appliedMemoryIds).toContain('interaction-3'); // 配送问题处理模式
    });

    test('应该能够识别和应用成功的解决方案模式', async () => {
      // 存储成功解决方案的程序性记忆
      const successfulProcedures: Memory[] = [
        {
          id: 'procedure-delivery-issue',
          type: 'procedural',
          content: 'Delivery Issue Resolution: 1. Acknowledge concern, 2. Check tracking, 3. Explain status, 4. Offer expedited shipping if delayed, 5. Provide compensation if appropriate, 6. Follow up',
          context: {
            domain: 'customer-service',
            procedure: 'delivery-issue-resolution',
            successRate: 0.92
          },
          importance: 0.95,
          createdAt: new Date('2024-01-10'),
          updatedAt: new Date('2024-01-18'),
          metadata: {
            tags: ['procedure', 'delivery', 'resolution', 'high-success'],
            validatedBy: 'performance-analysis'
          }
        },
        {
          id: 'procedure-complaint-handling',
          type: 'procedural',
          content: 'Complaint Handling: 1. Listen actively, 2. Empathize, 3. Apologize if appropriate, 4. Investigate issue, 5. Propose solution, 6. Confirm satisfaction, 7. Document for improvement',
          context: {
            domain: 'customer-service',
            procedure: 'complaint-handling',
            successRate: 0.88
          },
          importance: 0.9,
          createdAt: new Date('2024-01-12'),
          updatedAt: new Date('2024-01-18'),
          metadata: {
            tags: ['procedure', 'complaint', 'handling', 'empathy'],
            validatedBy: 'customer-feedback'
          }
        }
      ];

      for (const procedure of successfulProcedures) {
        await memorySystem.storeMemory(procedure);
      }

      // 复杂客户投诉场景
      const complexComplaintTask: Task = {
        type: 'customer-complaint',
        description: 'Customer received damaged product and is very upset, demanding full refund and compensation',
        requirements: [
          'Handle emotional customer',
          'Assess damage claim',
          'Determine appropriate compensation',
          'Restore customer confidence'
        ],
        context: {
          customerId: 'cust-004',
          issueType: 'damaged-product',
          customerMood: 'very-upset',
          orderValue: 300,
          damageLevel: 'significant'
        }
      };

      const enhancementResult = await memorySystem.enhanceAgent({
        agent: customerServiceAgent,
        task: complexComplaintTask,
        environment: {
          platform: 'phone',
          urgency: 'high'
        }
      });

      expect(enhancementResult.success).toBe(true);
      
      const enhancedAgent = enhancementResult.enhancedAgent!;
      
      // 验证程序性记忆被应用
      const proceduralMemories = enhancedAgent.memory.procedural;
      expect(proceduralMemories.length).toBeGreaterThan(0);
      
      const hasComplaintHandling = proceduralMemories.some(m => 
        m.content.includes('Complaint Handling') || 
        m.content.includes('Listen actively')
      );
      expect(hasComplaintHandling).toBe(true);
    });
  });

  describe('场景2: 教育助手个性化学习路径', () => {
    let educationAgent: Agent;

    beforeEach(() => {
      educationAgent = {
        id: 'education-assistant',
        name: 'Personalized Learning Assistant',
        type: 'education',
        capabilities: [
          'curriculum-planning',
          'progress-tracking',
          'adaptive-teaching',
          'assessment-analysis'
        ],
        knowledge: {
          facts: [
            'Different students have different learning styles',
            'Spaced repetition improves retention',
            'Active learning is more effective than passive learning'
          ],
          rules: [
            'Adapt teaching method to student learning style',
            'Provide immediate feedback on exercises',
            'Gradually increase difficulty based on mastery'
          ],
          procedures: [
            'Learning assessment procedure',
            'Personalized curriculum generation',
            'Progress evaluation workflow'
          ]
        },
        memory: {
          working: [],
          episodic: [],
          semantic: [],
          procedural: []
        },
        performance: {
          successRate: 0.73,
          averageResponseTime: 2000,
          taskCompletionRate: 0.79
        },
        metadata: {
          version: '1.5.0',
          lastUpdated: new Date(),
          specialization: 'personalized-education'
        }
      };
    });

    test('应该能够基于学生学习历史个性化教学', async () => {
      // 学生学习历史记忆
      const studentLearningHistory: Memory[] = [
        {
          id: 'student-001-math-session-1',
          type: 'episodic',
          content: 'Student struggled with algebra word problems but excelled at geometric visualization',
          context: {
            studentId: 'student-001',
            subject: 'mathematics',
            topic: 'algebra-geometry',
            performance: {
              algebra: 0.4,
              geometry: 0.9
            },
            learningStyle: 'visual',
            sessionDuration: 45
          },
          importance: 0.8,
          createdAt: new Date('2024-01-20'),
          updatedAt: new Date('2024-01-20'),
          metadata: {
            tags: ['mathematics', 'visual-learner', 'geometry-strength', 'algebra-weakness'],
            sessionType: 'assessment'
          }
        },
        {
          id: 'student-001-learning-pattern',
          type: 'semantic',
          content: 'Visual learners benefit from graphical representations and spatial reasoning exercises',
          context: {
            studentId: 'student-001',
            learningStyle: 'visual',
            effectiveMethods: ['diagrams', 'charts', 'spatial-exercises']
          },
          importance: 0.85,
          createdAt: new Date('2024-01-21'),
          updatedAt: new Date('2024-01-21'),
          metadata: {
            tags: ['visual-learning', 'teaching-method', 'effectiveness'],
            source: 'learning-analytics'
          }
        },
        {
          id: 'student-001-progress-tracking',
          type: 'episodic',
          content: 'After using visual aids for algebra, student performance improved from 40% to 75%',
          context: {
            studentId: 'student-001',
            subject: 'mathematics',
            topic: 'algebra',
            improvementMethod: 'visual-aids',
            performanceBefore: 0.4,
            performanceAfter: 0.75,
            timeframe: '2-weeks'
          },
          importance: 0.9,
          createdAt: new Date('2024-02-05'),
          updatedAt: new Date('2024-02-05'),
          metadata: {
            tags: ['improvement', 'visual-aids', 'algebra', 'success-story'],
            outcome: 'significant-improvement'
          }
        }
      ];

      for (const memory of studentLearningHistory) {
        await memorySystem.storeMemory(memory);
      }

      // 新的教学任务
      const teachingTask: Task = {
        type: 'personalized-lesson',
        description: 'Create a lesson plan for student-001 to learn quadratic equations',
        requirements: [
          'Adapt to student learning style',
          'Build on existing strengths',
          'Address known weaknesses',
          'Ensure engagement and understanding'
        ],
        context: {
          studentId: 'student-001',
          subject: 'mathematics',
          topic: 'quadratic-equations',
          difficulty: 'intermediate',
          timeAvailable: 60
        }
      };

      const enhancementResult = await memorySystem.enhanceAgent({
        agent: educationAgent,
        task: teachingTask,
        environment: {
          platform: 'online-classroom',
          resources: ['interactive-whiteboard', 'graphing-tools']
        }
      });

      expect(enhancementResult.success).toBe(true);
      
      const enhancedAgent = enhancementResult.enhancedAgent!;
      
      // 验证个性化适应
      const appliedMemories = enhancementResult.appliedMemories;
      const hasVisualLearningMemory = appliedMemories.some(m => 
        m.content.includes('visual') || m.metadata.tags?.includes('visual-learner')
      );
      expect(hasVisualLearningMemory).toBe(true);

      // 验证性能改进
      expect(enhancedAgent.performance.successRate).toBeGreaterThan(educationAgent.performance.successRate);
      
      // 验证记忆整合
      expect(enhancedAgent.memory.episodic.length).toBeGreaterThan(0);
      expect(enhancedAgent.memory.semantic.length).toBeGreaterThan(0);
    });

    test('应该能够跟踪多个学生的学习进度并优化教学策略', async () => {
      // 多个学生的学习数据
      const multiStudentData: Memory[] = [
        {
          id: 'class-analytics-1',
          type: 'semantic',
          content: 'Students who practice problems daily show 40% better retention than those who cram',
          context: {
            classId: 'math-101',
            pattern: 'daily-practice-vs-cramming',
            sampleSize: 30,
            retentionImprovement: 0.4
          },
          importance: 0.88,
          createdAt: new Date('2024-01-25'),
          updatedAt: new Date('2024-01-25'),
          metadata: {
            tags: ['retention', 'practice-frequency', 'class-analytics'],
            source: 'longitudinal-study'
          }
        },
        {
          id: 'teaching-strategy-effectiveness',
          type: 'semantic',
          content: 'Interactive problem-solving sessions result in 25% higher engagement than lecture-only format',
          context: {
            teachingMethod: 'interactive-vs-lecture',
            engagementIncrease: 0.25,
            applicableTo: ['mathematics', 'science', 'programming']
          },
          importance: 0.82,
          createdAt: new Date('2024-01-28'),
          updatedAt: new Date('2024-01-28'),
          metadata: {
            tags: ['engagement', 'interactive-learning', 'teaching-effectiveness'],
            validatedBy: 'classroom-experiments'
          }
        },
        {
          id: 'adaptive-difficulty-success',
          type: 'procedural',
          content: 'Adaptive Difficulty Procedure: 1. Assess current level, 2. Start slightly below mastery, 3. Increase difficulty after 80% success rate, 4. Decrease if success rate drops below 60%, 5. Provide hints before reducing difficulty',
          context: {
            procedure: 'adaptive-difficulty',
            successRate: 0.91,
            applicableTo: 'all-subjects'
          },
          importance: 0.93,
          createdAt: new Date('2024-02-01'),
          updatedAt: new Date('2024-02-01'),
          metadata: {
            tags: ['adaptive-learning', 'difficulty-adjustment', 'high-success'],
            validatedBy: 'multiple-classrooms'
          }
        }
      ];

      for (const memory of multiStudentData) {
        await memorySystem.storeMemory(memory);
      }

      // 课程规划任务
      const curriculumTask: Task = {
        type: 'curriculum-optimization',
        description: 'Optimize mathematics curriculum for improved student outcomes',
        requirements: [
          'Incorporate proven teaching strategies',
          'Implement adaptive difficulty',
          'Maximize student engagement',
          'Improve retention rates'
        ],
        context: {
          subject: 'mathematics',
          classSize: 25,
          duration: '16-weeks',
          targetImprovement: 0.3
        }
      };

      const enhancementResult = await memorySystem.enhanceAgent({
        agent: educationAgent,
        task: curriculumTask,
        environment: {
          platform: 'hybrid-classroom',
          technology: ['adaptive-learning-system', 'analytics-dashboard']
        }
      });

      expect(enhancementResult.success).toBe(true);
      
      const enhancedAgent = enhancementResult.enhancedAgent!;
      
      // 验证策略优化
      const appliedMemories = enhancementResult.appliedMemories;
      const hasAnalyticsMemory = appliedMemories.some(m => 
        m.content.includes('analytics') || m.content.includes('retention')
      );
      const hasAdaptiveMemory = appliedMemories.some(m => 
        m.content.includes('Adaptive Difficulty')
      );
      
      expect(hasAnalyticsMemory).toBe(true);
      expect(hasAdaptiveMemory).toBe(true);

      // 验证程序性知识整合
      const proceduralMemories = enhancedAgent.memory.procedural;
      const hasAdaptiveProcedure = proceduralMemories.some(m => 
        m.content.includes('Adaptive Difficulty Procedure')
      );
      expect(hasAdaptiveProcedure).toBe(true);
    });
  });

  describe('场景3: 项目管理助手风险预测和决策支持', () => {
    let projectManagerAgent: Agent;

    beforeEach(() => {
      projectManagerAgent = {
        id: 'project-manager-ai',
        name: 'AI Project Manager',
        type: 'project-management',
        capabilities: [
          'risk-assessment',
          'resource-planning',
          'timeline-optimization',
          'stakeholder-communication',
          'decision-support'
        ],
        knowledge: {
          facts: [
            'Software projects have 70% chance of scope creep',
            'Remote teams require 20% more communication overhead',
            'Critical path delays impact overall timeline directly'
          ],
          rules: [
            'Identify risks early in project lifecycle',
            'Maintain regular stakeholder communication',
            'Buffer critical path activities by 20%'
          ],
          procedures: [
            'Risk assessment workflow',
            'Project planning methodology',
            'Change management process'
          ]
        },
        memory: {
          working: [],
          episodic: [],
          semantic: [],
          procedural: []
        },
        performance: {
          successRate: 0.81,
          averageResponseTime: 1500,
          taskCompletionRate: 0.87
        },
        metadata: {
          version: '3.0.0',
          lastUpdated: new Date(),
          specialization: 'agile-project-management'
        }
      };
    });

    test('应该能够基于历史项目数据预测风险并提供决策支持', async () => {
      // 历史项目风险和结果记忆
      const projectHistoryMemories: Memory[] = [
        {
          id: 'project-alpha-risk-analysis',
          type: 'episodic',
          content: 'Project Alpha: Initial timeline 6 months, actual 9 months. Key risks: unclear requirements (materialized), key developer departure (materialized), third-party API changes (did not materialize)',
          context: {
            projectId: 'project-alpha',
            plannedDuration: 6,
            actualDuration: 9,
            delayFactor: 1.5,
            risks: {
              'unclear-requirements': { probability: 0.7, impact: 'high', materialized: true },
              'key-developer-departure': { probability: 0.3, impact: 'medium', materialized: true },
              'third-party-api-changes': { probability: 0.4, impact: 'low', materialized: false }
            },
            outcome: 'delayed-but-successful'
          },
          importance: 0.9,
          createdAt: new Date('2023-12-15'),
          updatedAt: new Date('2023-12-15'),
          metadata: {
            tags: ['project-history', 'risk-analysis', 'timeline-delay', 'lessons-learned'],
            projectType: 'web-application'
          }
        },
        {
          id: 'project-beta-success-factors',
          type: 'episodic',
          content: 'Project Beta: Completed on time and under budget. Success factors: detailed requirements gathering, experienced team, regular stakeholder reviews, proactive risk mitigation',
          context: {
            projectId: 'project-beta',
            plannedDuration: 4,
            actualDuration: 3.8,
            budgetVariance: -0.1,
            successFactors: [
              'detailed-requirements',
              'experienced-team',
              'regular-reviews',
              'proactive-risk-mitigation'
            ],
            outcome: 'highly-successful'
          },
          importance: 0.95,
          createdAt: new Date('2024-01-10'),
          updatedAt: new Date('2024-01-10'),
          metadata: {
            tags: ['project-success', 'best-practices', 'on-time-delivery', 'under-budget'],
            projectType: 'mobile-application'
          }
        },
        {
          id: 'risk-pattern-analysis',
          type: 'semantic',
          content: 'Projects with unclear requirements have 80% probability of timeline delays averaging 40% extension. Early requirements clarification reduces this risk to 15%',
          context: {
            riskType: 'unclear-requirements',
            delayProbability: 0.8,
            averageDelay: 0.4,
            mitigationEffectiveness: 0.85,
            sampleSize: 25
          },
          importance: 0.92,
          createdAt: new Date('2024-01-20'),
          updatedAt: new Date('2024-01-20'),
          metadata: {
            tags: ['risk-patterns', 'requirements-analysis', 'delay-prediction', 'mitigation'],
            source: 'project-analytics'
          }
        }
      ];

      for (const memory of projectHistoryMemories) {
        await memorySystem.storeMemory(memory);
      }

      // 新项目风险评估任务
      const riskAssessmentTask: Task = {
        type: 'project-risk-assessment',
        description: 'Assess risks for new e-commerce platform project and provide mitigation recommendations',
        requirements: [
          'Identify potential risks',
          'Estimate probability and impact',
          'Recommend mitigation strategies',
          'Provide timeline and budget adjustments'
        ],
        context: {
          projectType: 'e-commerce-platform',
          plannedDuration: 8,
          teamSize: 12,
          budget: 500000,
          stakeholders: ['product-owner', 'marketing', 'operations', 'customers'],
          technologies: ['react', 'node.js', 'postgresql', 'aws'],
          constraints: ['holiday-season-deadline', 'regulatory-compliance']
        }
      };

      const enhancementResult = await memorySystem.enhanceAgent({
        agent: projectManagerAgent,
        task: riskAssessmentTask,
        environment: {
          organization: 'enterprise',
          methodology: 'agile-scrum'
        }
      });

      expect(enhancementResult.success).toBe(true);
      
      const enhancedAgent = enhancementResult.enhancedAgent!;
      
      // 验证风险预测能力提升
      const appliedMemories = enhancementResult.appliedMemories;
      const hasRiskAnalysisMemory = appliedMemories.some(m => 
        m.content.includes('risk') || m.metadata.tags?.includes('risk-analysis')
      );
      expect(hasRiskAnalysisMemory).toBe(true);

      // 验证历史项目经验应用
      const hasProjectHistoryMemory = appliedMemories.some(m => 
        m.content.includes('Project Alpha') || m.content.includes('Project Beta')
      );
      expect(hasProjectHistoryMemory).toBe(true);

      // 验证性能改进
      expect(enhancedAgent.performance.successRate).toBeGreaterThan(projectManagerAgent.performance.successRate);
    });

    test('应该能够提供基于历史数据的决策支持', async () => {
      // 决策支持相关记忆
      const decisionSupportMemories: Memory[] = [
        {
          id: 'technology-choice-analysis',
          type: 'semantic',
          content: 'React-based projects show 30% faster development but 15% higher maintenance costs compared to Vue.js. Team experience is the primary success factor',
          context: {
            decisionType: 'technology-selection',
            options: ['react', 'vue.js'],
            metrics: {
              'development-speed': { react: 1.3, vue: 1.0 },
              'maintenance-cost': { react: 1.15, vue: 1.0 },
              'team-experience-impact': 0.4
            }
          },
          importance: 0.85,
          createdAt: new Date('2024-01-15'),
          updatedAt: new Date('2024-01-15'),
          metadata: {
            tags: ['technology-selection', 'react', 'vue', 'decision-support'],
            source: 'comparative-analysis'
          }
        },
        {
          id: 'team-scaling-decision',
          type: 'procedural',
          content: 'Team Scaling Decision Process: 1. Assess current velocity, 2. Identify bottlenecks, 3. Calculate onboarding time, 4. Consider communication overhead, 5. Evaluate budget impact, 6. Make incremental changes',
          context: {
            procedure: 'team-scaling',
            applicableWhen: 'project-acceleration-needed',
            considerations: ['velocity', 'bottlenecks', 'onboarding', 'communication', 'budget']
          },
          importance: 0.88,
          createdAt: new Date('2024-01-18'),
          updatedAt: new Date('2024-01-18'),
          metadata: {
            tags: ['team-scaling', 'decision-process', 'project-acceleration'],
            validatedBy: 'multiple-projects'
          }
        },
        {
          id: 'scope-change-impact-analysis',
          type: 'episodic',
          content: 'Mid-project scope changes averaging 25% increase in features resulted in 60% timeline extension and 40% budget overrun across 15 projects',
          context: {
            changeType: 'scope-expansion',
            averageIncrease: 0.25,
            timelineImpact: 0.6,
            budgetImpact: 0.4,
            sampleSize: 15
          },
          importance: 0.9,
          createdAt: new Date('2024-01-22'),
          updatedAt: new Date('2024-01-22'),
          metadata: {
            tags: ['scope-change', 'impact-analysis', 'timeline-extension', 'budget-overrun'],
            source: 'project-retrospectives'
          }
        }
      ];

      for (const memory of decisionSupportMemories) {
        await memorySystem.storeMemory(memory);
      }

      // 项目决策任务
      const decisionTask: Task = {
        type: 'project-decision-support',
        description: 'Client wants to add significant new features mid-project. Provide decision support with impact analysis',
        requirements: [
          'Analyze impact on timeline and budget',
          'Evaluate alternative approaches',
          'Recommend optimal decision',
          'Provide risk mitigation strategies'
        ],
        context: {
          currentProgress: 0.6,
          proposedChanges: {
            newFeatures: 8,
            complexity: 'high',
            estimatedEffort: '3-months'
          },
          constraints: {
            originalDeadline: '2024-06-01',
            budgetRemaining: 150000,
            teamCapacity: 'fully-utilized'
          },
          stakeholderPressure: 'high'
        }
      };

      const enhancementResult = await memorySystem.enhanceAgent({
        agent: projectManagerAgent,
        task: decisionTask,
        environment: {
          urgency: 'high',
          stakeholderMeeting: 'tomorrow'
        }
      });

      expect(enhancementResult.success).toBe(true);
      
      const enhancedAgent = enhancementResult.enhancedAgent!;
      
      // 验证决策支持记忆应用
      const appliedMemories = enhancementResult.appliedMemories;
      const hasScopeChangeMemory = appliedMemories.some(m => 
        m.content.includes('scope change') || m.content.includes('scope-expansion')
      );
      expect(hasScopeChangeMemory).toBe(true);

      // 验证程序性决策流程
      const proceduralMemories = enhancedAgent.memory.procedural;
      const hasDecisionProcess = proceduralMemories.some(m => 
        m.content.includes('Decision Process') || m.content.includes('scaling')
      );
      expect(hasDecisionProcess).toBe(true);

      // 验证决策支持能力提升
      expect(enhancedAgent.performance.successRate).toBeGreaterThan(projectManagerAgent.performance.successRate);
      expect(enhancementResult.performanceImprovement).toBeGreaterThan(0.1);
    });
  });

  describe('场景4: 跨场景记忆迁移和泛化', () => {
    test('应该能够将一个领域的经验迁移到相关领域', async () => {
      // 客服领域的沟通经验
      const customerServiceMemories: Memory[] = [
        {
          id: 'communication-best-practice',
          type: 'semantic',
          content: 'Active listening and empathy significantly improve customer satisfaction and problem resolution rates',
          context: {
            domain: 'customer-service',
            skill: 'communication',
            effectiveness: 0.85
          },
          importance: 0.9,
          createdAt: new Date('2024-01-10'),
          updatedAt: new Date('2024-01-10'),
          metadata: {
            tags: ['communication', 'empathy', 'active-listening', 'satisfaction'],
            transferable: true
          }
        },
        {
          id: 'conflict-resolution-technique',
          type: 'procedural',
          content: 'Conflict Resolution: 1. Remain calm, 2. Listen to all parties, 3. Identify common ground, 4. Focus on solutions not blame, 5. Confirm agreement, 6. Follow up',
          context: {
            domain: 'customer-service',
            technique: 'conflict-resolution',
            successRate: 0.88
          },
          importance: 0.87,
          createdAt: new Date('2024-01-12'),
          updatedAt: new Date('2024-01-12'),
          metadata: {
            tags: ['conflict-resolution', 'procedure', 'communication'],
            transferable: true
          }
        }
      ];

      for (const memory of customerServiceMemories) {
        await memorySystem.storeMemory(memory);
      }

      // 创建项目管理智能体（不同领域）
      const projectManagerAgent: Agent = {
        id: 'pm-agent-transfer-test',
        name: 'Project Manager for Transfer Test',
        type: 'project-management',
        capabilities: ['planning', 'coordination', 'risk-management'],
        knowledge: { facts: [], rules: [], procedures: [] },
        memory: { working: [], episodic: [], semantic: [], procedural: [] },
        performance: {
          successRate: 0.75,
          averageResponseTime: 1800,
          taskCompletionRate: 0.8
        },
        metadata: {
          version: '1.0.0',
          lastUpdated: new Date()
        }
      };

      // 项目管理中的团队冲突解决任务
      const teamConflictTask: Task = {
        type: 'team-conflict-resolution',
        description: 'Resolve conflict between development and QA teams regarding testing timelines',
        requirements: [
          'Understand both perspectives',
          'Find mutually acceptable solution',
          'Maintain team relationships',
          'Ensure project timeline adherence'
        ],
        context: {
          conflictType: 'process-disagreement',
          parties: ['development-team', 'qa-team'],
          issue: 'testing-timeline-disagreement',
          projectImpact: 'potential-delay'
        }
      };

      const enhancementResult = await memorySystem.enhanceAgent({
        agent: projectManagerAgent,
        task: teamConflictTask,
        environment: {
          urgency: 'medium',
          stakeholders: ['project-sponsor', 'team-leads']
        }
      });

      expect(enhancementResult.success).toBe(true);
      
      // 验证跨领域记忆迁移
      const appliedMemories = enhancementResult.appliedMemories;
      const hasTransferredMemory = appliedMemories.some(m => 
        m.content.includes('Conflict Resolution') || 
        m.content.includes('active listening') ||
        m.metadata.tags?.includes('conflict-resolution')
      );
      expect(hasTransferredMemory).toBe(true);

      const enhancedAgent = enhancementResult.enhancedAgent!;
      
      // 验证程序性知识迁移
      const proceduralMemories = enhancedAgent.memory.procedural;
      const hasConflictResolutionProcedure = proceduralMemories.some(m => 
        m.content.includes('Conflict Resolution:')
      );
      expect(hasConflictResolutionProcedure).toBe(true);

      // 验证性能提升
      expect(enhancedAgent.performance.successRate).toBeGreaterThan(projectManagerAgent.performance.successRate);
    });

    test('应该能够识别和应用通用模式', async () => {
      // 存储跨领域通用模式
      const universalPatterns: Memory[] = [
        {
          id: 'problem-solving-pattern',
          type: 'semantic',
          content: 'Systematic problem-solving approach: Define problem clearly, gather information, generate alternatives, evaluate options, implement solution, monitor results',
          context: {
            pattern: 'systematic-problem-solving',
            applicableDomains: ['customer-service', 'project-management', 'education', 'healthcare'],
            effectiveness: 0.92
          },
          importance: 0.95,
          createdAt: new Date('2024-01-05'),
          updatedAt: new Date('2024-01-05'),
          metadata: {
            tags: ['problem-solving', 'systematic-approach', 'universal-pattern'],
            transferable: true,
            validated: true
          }
        },
        {
          id: 'feedback-loop-pattern',
          type: 'semantic',
          content: 'Continuous improvement through feedback loops: Act, Measure, Learn, Adjust. Shorter cycles lead to faster improvement',
          context: {
            pattern: 'feedback-loop',
            cycleLength: 'variable',
            improvementRate: 'exponential',
            applicableTo: 'all-domains'
          },
          importance: 0.9,
          createdAt: new Date('2024-01-08'),
          updatedAt: new Date('2024-01-08'),
          metadata: {
            tags: ['feedback-loop', 'continuous-improvement', 'universal-pattern'],
            transferable: true
          }
        }
      ];

      for (const pattern of universalPatterns) {
        await memorySystem.storeMemory(pattern);
      }

      // 测试不同领域的智能体都能应用通用模式
      const testAgents = [
        {
          id: 'healthcare-agent',
          name: 'Healthcare Assistant',
          type: 'healthcare' as const,
          domain: 'healthcare'
        },
        {
          id: 'finance-agent',
          name: 'Financial Advisor',
          type: 'finance' as const,
          domain: 'finance'
        }
      ];

      for (const agentConfig of testAgents) {
        const agent: Agent = {
          id: agentConfig.id,
          name: agentConfig.name,
          type: agentConfig.type,
          capabilities: ['analysis', 'recommendation'],
          knowledge: { facts: [], rules: [], procedures: [] },
          memory: { working: [], episodic: [], semantic: [], procedural: [] },
          performance: {
            successRate: 0.7,
            averageResponseTime: 2000,
            taskCompletionRate: 0.75
          },
          metadata: {
            version: '1.0.0',
            lastUpdated: new Date(),
            domain: agentConfig.domain
          }
        };

        const problemSolvingTask: Task = {
          type: 'complex-problem-solving',
          description: `Solve a complex problem in ${agentConfig.domain} domain`,
          requirements: [
            'Analyze the situation systematically',
            'Generate multiple solution options',
            'Implement continuous improvement'
          ],
          context: {
            domain: agentConfig.domain,
            complexity: 'high',
            stakeholders: 'multiple'
          }
        };

        const enhancementResult = await memorySystem.enhanceAgent({
          agent,
          task: problemSolvingTask,
          environment: {
            domain: agentConfig.domain
          }
        });

        expect(enhancementResult.success).toBe(true);
        
        // 验证通用模式应用
        const appliedMemories = enhancementResult.appliedMemories;
        const hasUniversalPattern = appliedMemories.some(m => 
          m.metadata.tags?.includes('universal-pattern') ||
          m.content.includes('systematic problem-solving') ||
          m.content.includes('feedback loop')
        );
        expect(hasUniversalPattern).toBe(true);

        // 验证性能提升
        const enhancedAgent = enhancementResult.enhancedAgent!;
        expect(enhancedAgent.performance.successRate).toBeGreaterThan(agent.performance.successRate);
      }
    });
  });
});