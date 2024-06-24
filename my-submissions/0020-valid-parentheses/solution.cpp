#include <iostream>
#include <stack>
using namespace std;

class Solution {
public:
    bool isValid(string expression) {
        stack<char> s;
        for (char ch : expression) {
            if (ch == '(' || ch == '{' || ch == '[') {
                s.push(ch);
            } else {
                if (s.empty()) {
                    return false; // Unmatched closing bracket
                }
                char top = s.top();
                if ((ch == ')' && top == '(') || (ch == '}' && top == '{') || (ch == ']' && top == '[')) {
                     s.pop();
                } else {
                    return false; // Mismatched brackets
                }
            }
        }
        return s.empty(); // Check if all brackets are matched
    }
};

