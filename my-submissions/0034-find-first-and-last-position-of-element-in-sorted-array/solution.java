class Solution {
    public int[] searchRange(int[] nums, int target) {
      int first = searchfirstele(nums, target);
    int last = searchlastele(nums, target);
    return new int[] {first, last};

    }
    
    static int searchfirstele(int[] arr,int target) {
	int first=-1;
	int start=0;
	int end=arr.length-1;
	
	while(start<=end) {
		
		int mid=start+(end-start)/2;
		
		if(target==arr[mid]) {
			first=mid;
			end=mid-1;
		}else if(arr[mid]<target) {
			start=mid+1;
		}else {
			end=mid-1;
		}
	}
	return first;
}

static int searchlastele(int[] arr,int target) {
	int last=-1;
	int start=0;
	int end=arr.length-1;
	
	while(start<=end) {
		
		int mid=start+(end-start)/2;
		
		if(target==arr[mid]) {
			last=mid;
			start=mid+1;
		}else if(arr[mid]<target) {
			start=mid+1;
		}else {
			end=mid-1;
		}
	}
	return last;
}


}


