class Solution {
public:
    bool isPalindrome(int x) {
        if (x < 0) return false; // negative numbers are not palindromes
        int original = x; // store original value
        long long res = 0;
        while (x > 0) {
            int rem = x % 10;
            res = res * 10 + rem;
            x = x / 10;
        }
        return res == original; // compare with original value
    }
};


