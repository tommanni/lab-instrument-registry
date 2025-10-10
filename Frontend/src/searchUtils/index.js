import tokenize from './tokenize'
import createRpn from './createRPN'
import createTree from './createTree'
import Token from './token'

export function parseQueryToRpn(query) {
  const tokens = tokenize(query || '')
  return createRpn(tokens)
}

export function evaluateRpnBoolean(rpn, item, itemMatchesSingleTerm) {
  const stack = []
  for (const symbol of rpn) {
    if (Token.isTerm(symbol)) {
      stack.push(itemMatchesSingleTerm(symbol))
    } else if (Token.isOperator(symbol)) {
      if (symbol.operation === 'NOT') {
        const a = stack.pop() || false
        stack.push(!a)
      } else {
        const b = stack.pop() || false
        const a = stack.pop() || false
        stack.push(symbol.operation === 'AND' ? (a && b) : (a || b))
      }
    }
  }
  return Boolean(stack.pop())
}

export function parseQueryToTree(query) {
  const rpn = parseQueryToRpn(query)
  return createTree(rpn)
}


