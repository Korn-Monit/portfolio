const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class FakeNode {
    constructor(tagName = null, text = null) {
        this.tagName = tagName;
        this.text = text;
        this.childNodes = [];
        this.attributes = {};
    }

    appendChild(child) {
        this.childNodes.push(child);
        return child;
    }

    setAttribute(name, value) {
        this.attributes[name] = String(value);
    }
}

const document = {
    addEventListener() {},
    createDocumentFragment: () => new FakeNode('fragment'),
    createElement: tagName => new FakeNode(tagName),
    createTextNode: text => new FakeNode(null, text),
};

const context = {
    console,
    document,
    URL,
    window: { location: { hash: '' } },
};
vm.createContext(context);
const scriptPath = path.join(__dirname, '..', 'script.js');
vm.runInContext(fs.readFileSync(scriptPath, 'utf8'), context, { filename: scriptPath });

function snapshot(node) {
    if (node.text !== null) return node.text;
    const children = node.childNodes.map(snapshot).join('');
    if (node.tagName === 'fragment') return children;
    return `<${node.tagName}>${children}</${node.tagName}>`;
}

const parent = new FakeNode('p');
context.appendContentParts(parent, [
    { type: 'text', value: 'Start', styles: ['bold', 'italic'] },
    { type: 'link', label: 'link', url: 'https://example.com' },
    { type: 'text', value: '.', join: 'none' },
    { type: 'break' },
    { type: 'text', value: '<not HTML>' },
    { type: 'text', value: 'CV only', targets: ['cv'] },
], 'test');

assert.equal(
    snapshot(parent),
    '<p><strong><em>Start</em></strong> <a>link</a>.<br></br><not HTML></p>',
);
assert.equal(parent.childNodes[2].tagName, 'a');
assert.equal(parent.childNodes[2].href, 'https://example.com');
assert.equal(parent.childNodes[2].target, '_blank');
assert.equal(parent.childNodes[2].rel, 'noopener noreferrer');
assert.equal(parent.childNodes.at(-1).text, '<not HTML>');

assert.throws(
    () => context.appendContentParts(new FakeNode('p'), [
        { type: 'link', label: 'unsafe', url: 'javascript:alert(1)' },
    ], 'test'),
    /url is invalid/,
);

console.log('content renderer tests passed');
