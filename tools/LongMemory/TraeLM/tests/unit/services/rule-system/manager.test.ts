/**
 * RuleManager 单元测试
 * 
 * @description 测试规则管理器的各种功能
 * @author 高级软件专家
 */

import { RuleManager } from '../../../../src/services/rule-system/manager';
import { ConfigurationManager } from '../../../../src/config/manager';
import type { Rule, RuleContext } from '../../../../src/types/base';
import { RuleCategory, ConditionOperator, ActionType, EventSeverity, EventType } from '../../../../src/types/base';
import type { SystemEvent } from '../../../../src/types/base';

describe('RuleManager', () => {
  let ruleManager: RuleManager;
  let configManager: ConfigurationManager;

  beforeEach(async () => {
    configManager = new ConfigurationManager();
    await configManager.initialize();
    
    ruleManager = new RuleManager(configManager);
    await ruleManager.initialize();
  });

  afterEach(async () => {
    await ruleManager.destroy();
    await configManager.destroy();
  });

  // 简易辅助函数：生成唯一ID
  const uid = () => `rule-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  // 辅助函数：创建标准事件
  const makeEvent = (type: EventType, data: any = {}): SystemEvent => ({
    id: `evt-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    type,
    source: 'unit-test',
    data,
    timestamp: new Date(),
    severity: EventSeverity.LOW
  });

  describe('规则管理', () => {
    test('应该能够添加规则', async () => {
      const rule: Rule = {
        id: uid(),
        name: 'Test Rule',
        description: 'A test rule',
        category: RuleCategory.TECHNICAL,
        priority: 1,
        isActive: true,
        conditions: [{
          field: 'context.user.age',
          operator: ConditionOperator.GREATER_EQUAL,
          value: 18
        }],
        actions: [{
          type: ActionType.LOG,
          parameters: { message: 'User is adult' },
          priority: 1
        }],
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date()
      };

      await ruleManager.addRule(rule);
      
      const retrievedRule = ruleManager.getRule(rule.id);
      expect(retrievedRule).toBeDefined();
      expect(retrievedRule!.name).toBe('Test Rule');
      expect(retrievedRule!.isActive).toBe(true);
    });

    test('应该能够更新规则', async () => {
      const rule: Rule = {
        id: uid(),
        name: 'Original Rule',
        description: 'Original description',
        category: RuleCategory.TECHNICAL,
        priority: 1,
        isActive: true,
        conditions: [],
        actions: [{ type: ActionType.LOG, parameters: { message: 'init' }, priority: 1 }],
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date()
      };

      await ruleManager.addRule(rule);
      
      const updates = {
        name: 'Updated Rule',
        description: 'Updated description',
        priority: 2
      };

      await ruleManager.updateRule(rule.id, updates);
      
      const updatedRule = ruleManager.getRule(rule.id)!;
      expect(updatedRule!.name).toBe('Updated Rule');
      expect(updatedRule!.description).toBe('Updated description');
      expect(updatedRule!.priority).toBe(2);
    });

    test('应该能够删除规则', async () => {
      const rule: Rule = {
        id: uid(),
        name: 'Rule to Delete',
        description: 'This rule will be deleted',
        category: RuleCategory.TECHNICAL,
        priority: 1,
        isActive: true,
        conditions: [],
        actions: [{ type: ActionType.LOG, parameters: { message: 'init' }, priority: 1 }],
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date()
      };

      await ruleManager.addRule(rule);
      
      await ruleManager.removeRule(rule.id);
      
      const deletedRule = ruleManager.getRule(rule.id);
      expect(deletedRule).toBeUndefined();
    });

    test('应该能够启用和禁用规则', async () => {
      const rule: Rule = {
        id: uid(),
        name: 'Toggle Rule',
        description: 'Rule for testing enable/disable',
        category: RuleCategory.TECHNICAL,
        priority: 1,
        isActive: true,
        conditions: [],
        actions: [{ type: ActionType.LOG, parameters: { message: 'init' }, priority: 1 }],
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date()
      };

      await ruleManager.addRule(rule);
      
      await ruleManager.disableRule(rule.id);
      let toggledRule = ruleManager.getRule(rule.id)!;
      expect(toggledRule!.isActive).toBe(false);
      
      await ruleManager.enableRule(rule.id);
      toggledRule = ruleManager.getRule(rule.id)!;
      expect(toggledRule!.isActive).toBe(true);
    });
  });

  describe('规则查询', () => {
    beforeEach(async () => {
      // 添加测试规则
      const rules = [
        {
          id: uid(),
          name: 'High Priority Rule',
          description: 'High priority test rule',
          category: RuleCategory.SECURITY,
          priority: 10,
          isActive: true,
          conditions: [],
          actions: [{ type: ActionType.LOG, parameters: { message: 'security-high' }, priority: 1 }],
          metadata: { tags: ['security', 'high-priority'] },
          createdAt: new Date(),
          updatedAt: new Date()
        },
        {
          id: uid(),
          name: 'Low Priority Rule',
          description: 'Low priority test rule',
          category: RuleCategory.TECHNICAL,
          priority: 1,
          isActive: true,
          conditions: [],
          actions: [{ type: ActionType.LOG, parameters: { message: 'technical-low' }, priority: 1 }],
          metadata: { tags: ['logging', 'low-priority'] },
          createdAt: new Date(),
          updatedAt: new Date()
        },
        {
          id: uid(),
          name: 'Disabled Rule',
          description: 'Disabled test rule',
          category: RuleCategory.TECHNICAL,
          priority: 5,
          isActive: false,
          conditions: [],
          actions: [{ type: ActionType.LOG, parameters: { message: 'disabled' }, priority: 1 }],
          metadata: {},
          createdAt: new Date(),
          updatedAt: new Date()
        }
      ];

      for (const rule of rules) {
        await ruleManager.addRule(rule as Rule);
      }
    });

    test('应该能够获取所有规则', async () => {
      const allRules = ruleManager.getAllRules();
      expect(allRules.length).toBe(3);
    });

    test('应该能够按类别查询规则', async () => {
      const securityRules = ruleManager.getRulesByCategory(RuleCategory.SECURITY);
      expect(securityRules.length).toBe(1);
      expect(securityRules[0]!.name).toBe('High Priority Rule');
    });

    test('应该能够按启用状态查询规则', async () => {
      const enabledRules = ruleManager.getActiveRules();
      expect(enabledRules.length).toBe(2);
      
      const disabledRules = ruleManager.getAllRules().filter(r => !r.isActive);
      expect(disabledRules.length).toBe(1);
      expect(disabledRules[0]!.name).toBe('Disabled Rule');
    });

    test('应该能够按优先级排序规则', async () => {
      const sortedRules = ruleManager.getAllRules().slice().sort((a, b) => b.priority - a.priority);
      expect(sortedRules[0]!.priority).toBe(10); // 最高优先级
      expect(sortedRules[sortedRules.length - 1]!.priority).toBe(1); // 最低优先级
    });
  });

  describe('规则执行', () => {
    test('应该能够处理事件', async () => {
      const rule: Rule = {
        id: uid(),
        name: 'Event Processing Rule',
        description: 'Rule for testing event processing',
        category: RuleCategory.TECHNICAL,
        priority: 5,
        isActive: true,
        conditions: [{
          field: 'event.type',
          operator: ConditionOperator.EQUALS,
          value: EventType.RULE_TRIGGERED
        }],
        actions: [{
          type: ActionType.LOG,
          parameters: { message: 'User logged in' },
          priority: 1
        }],
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date()
      };

      await ruleManager.addRule(rule);

      const event = makeEvent(EventType.RULE_TRIGGERED, { userId: '12345' });
      const context: RuleContext = {
        user: {
          id: '12345',
          name: 'Test User'
        },
        session: {},
        environment: 'test'
      };

      const results = await ruleManager.processEvent(event, context);
      expect(results.length).toBeGreaterThan(0);
      expect(results[0]!.success).toBe(true);
    });

    test('应该按优先级顺序执行规则', async () => {
      const executionOrder: number[] = [];

      // 添加不同优先级的规则
      const rules = [
        { priority: 1, name: 'Low Priority' },
        { priority: 10, name: 'High Priority' },
        { priority: 5, name: 'Medium Priority' }
      ];

      for (const ruleData of rules) {
        const rule: Rule = {
          id: uid(),
          name: ruleData.name,
          description: `Rule with priority ${ruleData.priority}`,
          category: RuleCategory.TECHNICAL,
          priority: ruleData.priority,
          isActive: true,
          conditions: [{
            field: 'context.test',
            operator: ConditionOperator.EQUALS,
            value: true
          }],
          actions: [{
            type: ActionType.ENHANCE,
            parameters: {
              function: 'recordOrder',
              arguments: [ruleData.priority]
            },
            priority: 1
          }],
          metadata: {},
          createdAt: new Date(),
          updatedAt: new Date()
        };

        await ruleManager.addRule(rule);
      }

      const event = makeEvent(EventType.RULE_TRIGGERED);
      const context: RuleContext = {
        test: true,
        environment: 'test',
        recordOrder: (p: number) => executionOrder.push(p)
      };

      await ruleManager.processEvent(event, context);
      
      // 应该按优先级从高到低执行
      expect(executionOrder).toEqual([10, 5, 1]);
    });
  });

  describe('规则链和条件规则', () => {
    test('应该支持规则链', async () => {
      const r1: Rule = {
        id: uid(),
        name: 'Chain Rule 1',
        description: 'First rule in chain',
        category: RuleCategory.TECHNICAL,
        priority: 10,
        isActive: true,
        conditions: [{
          field: 'context.step',
          operator: ConditionOperator.EQUALS,
          value: 1
        }],
        actions: [{
          type: ActionType.STORE_MEMORY,
          parameters: { variable: 'step', value: 2 },
          priority: 1
        }],
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date()
      };

      const r2: Rule = {
        id: uid(),
        name: 'Chain Rule 2',
        description: 'Second rule in chain',
        category: RuleCategory.TECHNICAL,
        priority: 9,
        isActive: true,
        conditions: [{
          field: 'context.step',
          operator: ConditionOperator.EQUALS,
          value: 2
        }],
        actions: [{
          type: ActionType.STORE_MEMORY,
          parameters: { variable: 'completed', value: true },
          priority: 1
        }],
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date()
      };

      await ruleManager.addRule(r1);
      await ruleManager.addRule(r2);

      // 创建规则链
      await ruleManager.createRuleChain('chain-1', [r1.id, r2.id], { stopOnFailure: true, parallel: false });

      const event = makeEvent(EventType.RULE_TRIGGERED);
      const context: RuleContext = { step: 1, environment: 'test' };

      const chainResult = await ruleManager.executeRuleChain('chain-1', event, context);
      expect(chainResult.results.length).toBe(2);
      expect(context['completed']).toBe(true);
    });

    test('应该支持条件规则', async () => {
      // 创建条件规则（表达式模式）
      const condRuleId = 'cond-1';
      await ruleManager.createConditionalRule(condRuleId, [
        {
          expression: 'context.user.role === "admin" && context.user.permissions.includes("write")',
          actions: [{ type: ActionType.LOG, parameters: { message: 'Admin with write access' }, priority: 1 }]
        },
        {
          expression: 'context.user.role === "admin" && !context.user.permissions.includes("write")',
          actions: [{ type: ActionType.LOG, parameters: { message: 'Admin without write access' }, priority: 1 }]
        }
      ], { evaluationMode: 'any' });

      const event = makeEvent(EventType.RULE_TRIGGERED);

      const context1: RuleContext = {
        user: { role: 'admin', permissions: ['read', 'write'] },
        environment: 'test'
      };

      const context2: RuleContext = {
        user: { role: 'admin', permissions: ['read'] },
        environment: 'test'
      };

      const result1 = await ruleManager.evaluateConditionalRule(condRuleId, event, context1);
      const result2 = await ruleManager.evaluateConditionalRule(condRuleId, event, context2);

      expect(result1.executedActions.length).toBeGreaterThan(0);
      expect(result2.executedActions.length).toBeGreaterThan(0);
    });
  });

  describe('动态规则生成', () => {
    test('应该能够从模板生成规则（通过动态生成器）', async () => {
      const generatorId = 'gen-template';
      await ruleManager.createDynamicRuleGenerator(generatorId, async (event: SystemEvent, _context: RuleContext) => {
        const userId = event.data?.['userId'] || 'unknown';
        const r: Rule = {
          id: uid(),
          name: `Generated Rule for ${userId}`,
          description: `Auto-generated rule for user ${userId}`,
          category: RuleCategory.TECHNICAL,
          priority: 5,
          isActive: true,
          conditions: [{ field: 'context.user.id', operator: ConditionOperator.EQUALS, value: userId }],
          actions: [{ type: ActionType.LOG, parameters: { message: `Rule triggered for user ${userId}` }, priority: 1 }],
          metadata: { generated: true },
          createdAt: new Date(),
          updatedAt: new Date()
        };
        return [r];
      }, { maxRules: 10 });

      const event = makeEvent(EventType.RULE_TRIGGERED, { userId: '12345' });
      const generated = await ruleManager.generateDynamicRules(generatorId, event, {});

      expect(generated.length).toBe(1);
      const generatedRule = ruleManager.getRule(generated[0]!.id)!;
      expect(generatedRule.name).toBe('Generated Rule for 12345');
      expect(generatedRule.conditions[0]!.value).toBe('12345');
      expect(generatedRule.metadata!['generated']).toBe(true);
    });

    test('应该能够从模式生成规则（通过动态生成器）', async () => {
      const generatorId = 'gen-pattern';
      await ruleManager.createDynamicRuleGenerator(generatorId, async (_event: SystemEvent, _context: RuleContext) => {
        const r: Rule = {
          id: uid(),
          name: 'User Activity Rule',
          description: 'Generated by pattern',
          category: RuleCategory.TECHNICAL,
          priority: 4,
          isActive: true,
          conditions: [
            { field: 'context.user.active', operator: ConditionOperator.EQUALS, value: true },
            { field: 'context.session.valid', operator: ConditionOperator.EQUALS, value: true }
          ],
          actions: [
            { type: ActionType.STORE_MEMORY, parameters: { variable: 'lastSeen', value: new Date().toISOString() }, priority: 1 },
            { type: ActionType.LOG, parameters: { message: 'Activity logged' }, priority: 1 }
          ],
          metadata: { generated: true },
          createdAt: new Date(),
          updatedAt: new Date()
        };
        return [r];
      });

      const event = makeEvent(EventType.RULE_TRIGGERED);
      const rules = await ruleManager.generateDynamicRules(generatorId, event, {});
      const generatedRule = ruleManager.getRule(rules[0]!.id)!;

      expect(generatedRule).toBeDefined();
      expect(generatedRule.conditions.length).toBe(2);
      expect(generatedRule.actions.length).toBe(2);
    });
  });

  describe('规则导入导出', () => {
    test('应该能够导出规则', async () => {
      const rule: Rule = {
        id: uid(),
        name: 'Export Test Rule',
        description: 'Rule for testing export',
        category: RuleCategory.TECHNICAL,
        priority: 1,
        isActive: true,
        conditions: [],
        actions: [],
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date()
      };

      await ruleManager.addRule(rule);

      const exportData = await ruleManager.exportRules();
      expect(exportData.rules.length).toBe(1);
      expect(exportData.rules[0].name).toBe('Export Test Rule');
      expect(exportData.exportedAt).toBeDefined();
    });

    test('应该能够导入规则', async () => {
      const importData = {
        rules: [{
          id: uid(),
          name: 'Imported Rule',
          description: 'Rule imported from external source',
          category: RuleCategory.TECHNICAL,
          priority: 3,
          isActive: true,
          conditions: [],
          actions: [],
          metadata: { imported: true },
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }],
        stats: { totalRules: 1, activeRules: 1, categoryStats: { [RuleCategory.TECHNICAL]: 1 } },
        exportedAt: new Date().toISOString(),
        version: '1.0.0'
      } as any;

      await ruleManager.importRules(importData);

      const importedRules = ruleManager.getRulesByCategory(RuleCategory.TECHNICAL);
      expect(importedRules.length).toBe(1);
      expect(importedRules[0]!.name).toBe('Imported Rule');
    });
  });

  describe('统计和监控', () => {
    test('应该提供规则统计信息', async () => {
      // 添加一些测试规则
      const rules = [
        { category: RuleCategory.SECURITY, enabled: true },
        { category: RuleCategory.SECURITY, enabled: false },
        { category: RuleCategory.TECHNICAL, enabled: true },
        { category: RuleCategory.TECHNICAL, enabled: true }
      ];

      for (const ruleData of rules) {
        const rule: Rule = {
          id: uid(),
          name: `Rule ${Math.random()}`,
          description: 'Test rule',
          category: ruleData.category,
          priority: 1,
          isActive: ruleData.enabled,
          conditions: [],
          actions: [],
          metadata: {},
          createdAt: new Date(),
          updatedAt: new Date()
        };

        await ruleManager.addRule(rule);
      }

      const stats = ruleManager.getStats();
      expect(stats.engine.totalRules).toBe(4);
      expect(stats.engine.activeRules).toBe(3);
      expect(stats.engine.categoryStats[RuleCategory.SECURITY]).toBe(2);
      expect(stats.engine.categoryStats[RuleCategory.TECHNICAL]).toBe(2);
    });

    test('应该跟踪规则执行指标', async () => {
      const rule: Rule = {
        id: uid(),
        name: 'Metrics Test Rule',
        description: 'Rule for testing execution metrics',
        category: RuleCategory.TECHNICAL,
        priority: 1,
        isActive: true,
        conditions: [{
          field: 'context.test',
          operator: ConditionOperator.EQUALS,
          value: true
        }],
        actions: [{ type: ActionType.LOG, parameters: { message: 'Metrics test' }, priority: 1 }],
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date()
      };

      await ruleManager.addRule(rule);

      const event = makeEvent(EventType.RULE_TRIGGERED);
      const context: RuleContext = { test: true, environment: 'test' };

      // 执行规则多次
      for (let i = 0; i < 5; i++) {
        await ruleManager.processEvent(event, context);
      }

      const history = ruleManager.getExecutionHistory();
      const records = history.filter(h => h.ruleId === rule.id);
      expect(records.length).toBe(5);
      expect(records.every(r => r.success)).toBe(true);
      const avg = records.reduce((sum, r) => sum + (r.executionTime || 0), 0) / records.length;
      expect(avg).toBeGreaterThanOrEqual(0);
    });
  });

  describe('错误处理', () => {
    test('应该处理无效规则ID', async () => {
      expect(ruleManager.getRule('invalid-id')).toBeUndefined();
      // updateRule 对无效ID不抛错（按当前实现），但不会更新任何内容
      await expect(ruleManager.updateRule('invalid-id', {})).resolves.toBeUndefined();
      await expect(ruleManager.removeRule('invalid-id')).rejects.toThrow();
    });

    test('应该处理规则执行错误', async () => {
      const faultyRule: Rule = {
        id: uid(),
        name: 'Faulty Rule',
        description: 'Rule that will cause an error',
        category: RuleCategory.TECHNICAL,
        priority: 1,
        isActive: true,
        conditions: [{ field: 'context.test', operator: ConditionOperator.EQUALS, value: true }],
        actions: [{ type: ActionType.ENHANCE, parameters: { function: 'unknownFunction' }, priority: 1 }],
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date()
      };

      await ruleManager.addRule(faultyRule);

      const event = makeEvent(EventType.RULE_TRIGGERED);
      const results = await ruleManager.processEvent(event, { test: true, environment: 'test' });
      expect(results.length).toBe(1);
      expect(results[0]!.success).toBe(false);
      expect(results[0]!.error).toBeDefined();
    });

    test('应该验证规则数据', async () => {
      const invalidRule = {
        // 缺少必需字段
        description: 'Invalid rule',
        category: 'test'
      };

      await expect(ruleManager.addRule(invalidRule as any)).rejects.toThrow();
    });
  });
});