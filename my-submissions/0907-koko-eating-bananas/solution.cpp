class Solution {
public:
    long long calculateTotalHours(vector<int> &v,int hourly){
        int n=v.size();
        long long totalHours=0;
        for(int i=0;i<n;i++){
            totalHours=totalHours+ceil((double)v[i]/(double)hourly);
        }
        return totalHours;
    }
    int findMax(vector<int> &v){
        int maxi=0;
        int n=v.size();
        for(int i=0;i<n;i++){
                maxi=max(maxi,v[i]);
        }
        return maxi;
    }
    int minEatingSpeed(vector<int>& piles, int h) {
        int low=1,high=findMax(piles);
        while(low<=high){
            int mid=low+(high-low)/2;
            long long totalHours=calculateTotalHours(piles,mid);
            if(totalHours<=h){
                high=mid-1;
            }else{
                low=mid+1;
            }
        }
        return low;
    }
};

    
