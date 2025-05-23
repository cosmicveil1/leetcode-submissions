class Solution {
    public int findNumbers(int[] nums) {
      int count=0;
	for(int num:nums) {
		if(evennum(num)) {
		count++;	
	}
}
	return count;
}

static boolean evennum(int num) {
	if(countdig(num)%2==0) {
		return true;
	}
	return false;
}



static int countdig(int number) {
	if(number<0) {
		number=number*-1;
	}
	int count=0;
	while(number>0) {
		count++;
		number=number/10;	
	}
	return count;
}



}
  
    

