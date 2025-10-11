import Token from './token'

// Tokenize a boolean query string into Token instances
// Supports quotes for phrases, parentheses, AND/OR/NOT (case-insensitive), and '!' as NOT
export default function tokenize(query) {
  const tokens = []
  const s = String(query)
  const len = s.length
  let i = 0

  const isWhitespace = (ch) => /\s/.test(ch)

  while (i < len) {
    const ch = s[i]

    // Skip whitespace
    if (isWhitespace(ch)) {
      i += 1
      continue
    }

    // Quoted phrase (unqualified)
    if (ch === '"') {
      let j = i + 1
      let value = ''
      while (j < len && s[j] !== '"') {
        // basic escape for \" not implemented; assume simple quotes
        value += s[j]
        j += 1
      }
      // j now at closing quote or end
      const endIndex = j < len && s[j] === '"' ? j : j - 1
      tokens.push(Token.create(value, 'term', endIndex, undefined))
      i = (j < len ? j + 1 : j)
      continue
    }

    // Parentheses
    if (ch === '(') {
      tokens.push(Token.create('(', 'grouping', i, 'open'))
      i += 1
      continue
    }
    if (ch === ')') {
      tokens.push(Token.create(')', 'grouping', i, 'close'))
      i += 1
      continue
    }

    // '!' as NOT (unary)
    if (ch === '!') {
      tokens.push(Token.create('NOT', 'operator', i, 'NOT'))
      i += 1
      continue
    }

    // Multi-letter operators AND/OR/NOT
    // Match longest first
    const rest = s.slice(i)
    const mOp = /^(AND|OR|NOT)\b/i.exec(rest)
    if (mOp) {
      const op = mOp[1].toUpperCase()
      const endIndex = i + mOp[0].length - 1
      tokens.push(Token.create(op, 'operator', endIndex, op))
      i += mOp[0].length
      continue
    }

    // Field-qualified term: field:value or field:"multi word"
    // field name: letters, numbers, underscore
    const mField = /^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*/.exec(rest)
    if (mField) {
      const fieldName = mField[1]
      i += mField[0].length
      if (i < len && s[i] === '"') {
        // quoted value
        let j = i + 1
        let value = ''
        while (j < len && s[j] !== '"') {
          value += s[j]
          j += 1
        }
        const endIndex = j < len && s[j] === '"' ? j : j - 1
        tokens.push(Token.create(value, 'term', endIndex, undefined, fieldName))
        i = (j < len ? j + 1 : j)
        continue
      } else {
        // unquoted value runs until whitespace or special char
        let j = i
        let value = ''
        const isStopChar = (c) => /[\s()]/.test(c)
        while (j < len && !isStopChar(s[j])) {
          value += s[j]
          j += 1
        }
        const endIndex = j - 1
        if (value) {
          tokens.push(Token.create(value, 'term', endIndex, undefined, fieldName))
        }
        i = j
        continue
      }
    }

    // Term: read until whitespace or special char
    let j = i
    let value = ''
    const isStopChar = (c) => /[\s()]/.test(c)
    while (j < len && !isStopChar(s[j])) {
      value += s[j]
      j += 1
    }
    const endIndex = j - 1
    if (value) {
      tokens.push(Token.create(value, 'term', endIndex, undefined))
    }
    i = j
  }

  return tokens
}


