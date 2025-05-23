class Solution {
    public int maximumWealth(int[][] accounts) {
       int ans=Integer.MIN_VALUE;
      for(int person=0;person<accounts.length;person++) {
			int rowsum=0;
			for(int account=0;account<accounts[person].length;account++) {
			 rowsum=rowsum+accounts[person][account];
			}
			if(rowsum>ans) {
				ans=rowsum;
		}
}
	return ans;
    }
}
