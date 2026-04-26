/**
 * Definition for a binary tree node.
 * struct TreeNode {
 *     int val;
 *     TreeNode *left;
 *     TreeNode *right;
 *     TreeNode() : val(0), left(nullptr), right(nullptr) {}
 *     TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
 *     TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
 * };
 */
class Solution {
public:
    bool isBalanced(TreeNode* root) {
        return maXdepth(root)!=-1;
    }
    int maXdepth(TreeNode* root){
        if(root==NULL) return 0;

        int leftside=maXdepth(root->left);
        if(leftside==-1) return -1;
        int rightside=maXdepth(root->right);
        if(rightside==-1) return -1;

        if(abs(rightside-leftside)>1) return -1;
        return max(leftside,rightside)+1;


    }
};
