class Solution {
public:
    void reverseString(vector<char>& s) {
        int n=s.size();
        for(int i=0;i<n;i++){
            if(i>=n/2)
             return;
        
        swap(s[i],s[n-i-1]);
        }
       
    }
};
