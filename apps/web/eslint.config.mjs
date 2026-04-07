import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

const TEST_CALL_NAMES = new Set(["test", "it"]);

function isIdentifierNamed(node, name) {
  return node?.type === "Identifier" && node.name === name;
}

function isTestCallExpression(node) {
  if (node?.type !== "CallExpression") {
    return false;
  }
  const { callee } = node;
  if (callee?.type === "Identifier") {
    return TEST_CALL_NAMES.has(callee.name);
  }
  if (
    callee?.type === "MemberExpression" &&
    !callee.computed &&
    callee.object?.type === "Identifier"
  ) {
    return TEST_CALL_NAMES.has(callee.object.name);
  }
  return false;
}

function isTestCallbackFunction(node) {
  return node?.type === "ArrowFunctionExpression" || node?.type === "FunctionExpression";
}

function findEnclosingTestCallback(ancestors) {
  for (let index = ancestors.length - 1; index >= 0; index -= 1) {
    const node = ancestors[index];
    if (!isTestCallbackFunction(node)) {
      continue;
    }
    const parent = ancestors[index - 1];
    if (parent?.type === "CallExpression" && isTestCallExpression(parent)) {
      return { callback: node, callbackIndex: index };
    }
  }
  return null;
}

function hasExpectCall(node) {
  if (!node || typeof node !== "object") {
    return false;
  }
  const stack = [node];
  const visited = new WeakSet();

  while (stack.length > 0) {
    const current = stack.pop();
    if (!current || typeof current !== "object") {
      continue;
    }
    if (visited.has(current)) {
      continue;
    }
    visited.add(current);

    if (current.type === "CallExpression" && isIdentifierNamed(current.callee, "expect")) {
      return true;
    }

    for (const value of Object.values(current)) {
      if (!value) {
        continue;
      }
      if (Array.isArray(value)) {
        for (const child of value) {
          if (child && typeof child === "object" && "type" in child) {
            stack.push(child);
          }
        }
        continue;
      }
      if (typeof value === "object" && "type" in value) {
        stack.push(value);
      }
    }
  }
  return false;
}

const testQualityPlugin = {
  rules: {
    "require-expect": {
      meta: {
        type: "problem",
        docs: { description: "Require at least one expect() assertion in each test callback." },
        schema: [],
      },
      create(context) {
        return {
          CallExpression(node) {
            if (!isTestCallExpression(node)) {
              return;
            }
            const callback = node.arguments.find(isTestCallbackFunction);
            if (!callback) {
              return;
            }
            if (hasExpectCall(callback.body)) {
              return;
            }
            context.report({
              node: callback,
              message: "Test callback must include at least one expect() assertion.",
            });
          },
        };
      },
    },
    "no-conditional-expect": {
      meta: {
        type: "problem",
        docs: { description: "Disallow expect() inside conditional branches." },
        schema: [],
      },
      create(context) {
        return {
          CallExpression(node) {
            if (!isIdentifierNamed(node.callee, "expect")) {
              return;
            }
            const ancestors = context.sourceCode.getAncestors(node);
            const contextInfo = findEnclosingTestCallback(ancestors);
            if (!contextInfo) {
              return;
            }
            const { callbackIndex } = contextInfo;
            const conditionalAncestor = ancestors.slice(callbackIndex + 1).find((ancestor) => {
              return (
                ancestor.type === "IfStatement" ||
                ancestor.type === "SwitchCase" ||
                ancestor.type === "ConditionalExpression" ||
                ancestor.type === "LogicalExpression"
              );
            });

            if (!conditionalAncestor) {
              return;
            }
            context.report({
              node,
              message: "Do not place expect() inside conditional branches.",
            });
          },
        };
      },
    },
    "valid-expect-promise": {
      meta: {
        type: "problem",
        docs: {
          description:
            "Require promise assertions using expect(...).resolves/rejects to be awaited or returned.",
        },
        schema: [],
      },
      create(context) {
        return {
          CallExpression(node) {
            if (!isIdentifierNamed(node.callee, "expect")) {
              return;
            }
            const ancestors = context.sourceCode.getAncestors(node);
            const contextInfo = findEnclosingTestCallback(ancestors);
            if (!contextInfo) {
              return;
            }
            const { callback, callbackIndex } = contextInfo;
            const inPromiseAssertionChain = ancestors.slice(callbackIndex + 1).some((ancestor) => {
              return (
                ancestor.type === "MemberExpression" &&
                !ancestor.computed &&
                ancestor.property.type === "Identifier" &&
                (ancestor.property.name === "resolves" || ancestor.property.name === "rejects")
              );
            });
            if (!inPromiseAssertionChain) {
              return;
            }

            const hasAwaitOrReturn = ancestors.slice(callbackIndex + 1).some((ancestor) => {
              return ancestor.type === "AwaitExpression" || ancestor.type === "ReturnStatement";
            });
            const isImplicitReturnArrow =
              callback.type === "ArrowFunctionExpression" && callback.body.type !== "BlockStatement";

            if (hasAwaitOrReturn || isImplicitReturnArrow) {
              return;
            }
            context.report({
              node,
              message:
                "Promise assertions with expect(...).resolves/rejects must be awaited or returned.",
            });
          },
        };
      },
    },
  },
};

export default [
  ...nextCoreWebVitals,
  ...nextTypeScript,
  {
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/preserve-manual-memoization": "off",
      "react-hooks/incompatible-library": "off",
    },
  },
  {
    files: ["**/*.test.{js,jsx,ts,tsx,mjs,cjs}", "**/*.spec.{js,jsx,ts,tsx,mjs,cjs}"],
    plugins: {
      "test-quality": testQualityPlugin,
    },
    rules: {
      "test-quality/require-expect": "error",
      "test-quality/no-conditional-expect": "error",
      "test-quality/valid-expect-promise": "error",
    },
  },
];
